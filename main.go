package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/aws/aws-lambda-go/lambda"
	"github.com/joho/godotenv"
	"github.com/line/line-bot-sdk-go/v7/linebot"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type Env struct {
	clientId               string
	clientSecret           string
	lineChannelAccessToken string
	lineChannelSecret      string
	channelName            string
	url                    string
	mongodbUri             string
}

type Token struct {
	AccessToken string `json:"access_token"`
}

type ChannelData struct {
	Channels []*Channel `json:"data"`
}
type Channel struct {
	BroadcasterLanguage string        `json:"broadcaster_language"`
	BroadcasterLogin    string        `json:"broadcaster_login"`
	DisplayName         string        `json:"display_name"`
	GameID              string        `json:"game_id"`
	GameName            string        `json:"game_name"`
	ID                  string        `json:"id"`
	IsLive              bool          `json:"is_live"`
	TagIds              []interface{} `json:"tag_ids"`
	ThumbnailURL        string        `json:"thumbnail_url"`
	Title               string        `json:"title"`
	StartedAt           string        `json:"started_at"`
}

type LiveData struct {
	Live []*Live `json:"data"`
}

type Live struct {
	ID           string    `json:"id"`
	UserID       string    `json:"user_id"`
	UserLogin    string    `json:"user_login"`
	UserName     string    `json:"user_name"`
	GameID       string    `json:"game_id"`
	GameName     string    `json:"game_name"`
	Type         string    `json:"type"`
	Title        string    `json:"title"`
	ViewerCount  int       `json:"viewer_count"`
	StartedAt    time.Time `json:"started_at"`
	Language     string    `json:"language"`
	ThumbnailURL string    `json:"thumbnail_url"`
	TagIds       []string  `json:"tag_ids"`
	IsMature     bool      `json:"is_mature"`
}

type Data struct {
	Id       primitive.ObjectID `json:"id" bson:"_id"`
	LiveTime string             `json: "liveTime" bson: "liveTime"`
}

// 環境変数取得
func getEnv() (env *Env, err error) {
	if os.Getenv("APP_ENV") != "production" && os.Getenv("CI_ENV") != "TRUE" {
		err = godotenv.Load(".env")

		if err != nil {
			return
		}
	}

	env = new(Env)
	env.clientId = os.Getenv("CLIENT_ID")
	env.clientSecret = os.Getenv("CLIENT_SECRET")
	env.lineChannelAccessToken = os.Getenv("LINE_CHANNEL_ACCESS_TOKEN")
	env.lineChannelSecret = os.Getenv("LINE_CHANNEL_SECRET")
	env.channelName = "kato_junichi0817"
	env.url = "https://www.twitch.tv/" + env.channelName
	env.mongodbUri = os.Getenv("MONGODB_URI")

	return
}

// トークン取得
func getToken(env *Env) (token *Token, err error) {
	fmt.Println("トークン取得")
	data := url.Values{
		"client_id":     []string{env.clientId},
		"client_secret": []string{env.clientSecret},
		"grant_type":    []string{"client_credentials"},
		"scope":         []string{"channel:read:stream_key"},
	}

	resp, err := http.PostForm("https://id.twitch.tv/oauth2/token", data)

	if err != nil {
		return
	}

	defer resp.Body.Close()

	b, err := io.ReadAll(resp.Body)

	if err != nil {
		return
	}

	token = new(Token)

	_ = json.Unmarshal(b, token)

	return
}

// チャンネル情報取得
func getChannel(env *Env, token *Token) (*Channel, error) {
	fmt.Println("チャンネル取得")

	req, _ := http.NewRequest(http.MethodGet, "https://api.twitch.tv/helix/search/channels?query="+env.channelName, nil)
	req.Header.Set("Client-ID", env.clientId)
	req.Header.Set("Authorization", "Bearer "+token.AccessToken)

	client := new(http.Client)
	resp, err := client.Do(req)

	if err != nil {
		return nil, err
	}

	defer resp.Body.Close()

	b, err := io.ReadAll(resp.Body)

	if err != nil {
		return nil, err
	}

	data := new(ChannelData)

	_ = json.Unmarshal(b, data)

	for _, c := range data.Channels {
		if c.BroadcasterLogin == env.channelName {
			return c, nil
		}
	}

	return nil, err
}

// 配信情報取得
func getLive(env *Env, token *Token, channel *Channel) (*Live, error) {
	fmt.Println("配信情報取得")

	req, _ := http.NewRequest(http.MethodGet, "https://api.twitch.tv/helix/streams?user_id="+channel.ID, nil)
	req.Header.Set("Client-ID", env.clientId)
	req.Header.Set("Authorization", "Bearer "+token.AccessToken)

	client := new(http.Client)
	resp, err := client.Do(req)

	if err != nil {
		return nil, err
	}

	defer resp.Body.Close()

	b, err := io.ReadAll(resp.Body)

	if err != nil {
		return nil, err
	}

	data := new(LiveData)

	_ = json.Unmarshal(b, data)

	if len(data.Live) == 0 {
		return nil, fmt.Errorf("未配信です")
	}

	if data.Live[0].GameName == "" {
		data.Live[0].GameName = "未設定"
	}

	return data.Live[0], nil
}

// mongodbコレクション取得
func getOldLiveTime(env *Env, live *Live) (string, error) {
	fmt.Println("配信時間取得")

	serverAPIOptions := options.ServerAPI(options.ServerAPIVersion1)
	clientOptions := options.Client().
		ApplyURI(env.mongodbUri).
		SetServerAPIOptions(serverAPIOptions)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	client, err := mongo.Connect(ctx, clientOptions)
	if err != nil {
		return "", err
	}
	defer client.Disconnect(ctx)

	coll := client.Database("jrb").Collection("liveInfo")
	var data Data
	filter := bson.D{{"userId", 1}}
	err = coll.FindOne(context.TODO(), filter).Decode(&data)
	if err != nil {
		return "", err
	}

	jst := time.FixedZone("Asia/Tokyo", 9*60*60)
	liveTime := live.StartedAt.In(jst).Format("2006/01/02 15:04") + " 開始"

	if data.LiveTime == liveTime {
		return "", fmt.Errorf("通知済みです")
	}

	_, err = coll.UpdateOne(context.TODO(), filter, bson.D{{"$set", bson.D{{"liveTime", liveTime}}}})
	if err != nil {
		return "", err
	}

	return liveTime, nil
}

// メッセージ送信
func sendMessage(env *Env, live *Live, liveTime string) (err error) {
	client, err := linebot.New(env.lineChannelSecret, env.lineChannelAccessToken)

	if err != nil {
		return
	}

	message := linebot.NewFlexMessage(
		"「"+live.Title+"」が開始しました",
		&linebot.BubbleContainer{
			Type: linebot.FlexContainerTypeBubble,
			Hero: &linebot.ImageComponent{
				Type:        linebot.FlexComponentTypeImage,
				URL:         strings.ReplaceAll(strings.ReplaceAll(live.ThumbnailURL, "{width}", "320"), "{height}", "180"),
				Size:        linebot.FlexImageSizeTypeFull,
				AspectRatio: linebot.FlexImageAspectRatioType3to1,
				AspectMode:  linebot.FlexImageAspectModeTypeCover,
				Action: &linebot.URIAction{
					URI: env.url,
				},
			},
			Body: &linebot.BoxComponent{
				Type:    linebot.FlexComponentTypeBox,
				Layout:  linebot.FlexBoxLayoutTypeVertical,
				Spacing: linebot.FlexComponentSpacingTypeMd,
				Action: &linebot.URIAction{
					URI: env.url,
				},
				Contents: []linebot.FlexComponent{
					&linebot.TextComponent{
						Type:  linebot.FlexComponentTypeText,
						Text:  "Twitchで配信開始しました",
						Size:  linebot.FlexTextSizeTypeXxs,
						Color: "#ff0000",
					},
					&linebot.TextComponent{
						Type: linebot.FlexComponentTypeText,
						Text: liveTime,
						Size: linebot.FlexTextSizeTypeXs,
					},
					&linebot.TextComponent{
						Type:   linebot.FlexComponentTypeText,
						Text:   live.Title,
						Size:   linebot.FlexTextSizeTypeXl,
						Weight: linebot.FlexTextWeightTypeBold,
					},
					&linebot.BoxComponent{
						Type:    linebot.FlexComponentTypeBox,
						Layout:  linebot.FlexBoxLayoutTypeVertical,
						Spacing: linebot.FlexComponentSpacingTypeSm,
						Contents: []linebot.FlexComponent{
							&linebot.BoxComponent{
								Type:   linebot.FlexComponentTypeBox,
								Layout: linebot.FlexBoxLayoutTypeBaseline,
								Contents: []linebot.FlexComponent{
									&linebot.TextComponent{
										Type:  linebot.FlexComponentTypeText,
										Text:  live.GameName,
										Size:  linebot.FlexTextSizeTypeSm,
										Align: linebot.FlexComponentAlignTypeStart,
										Color: "#aaaaaa",
									},
								},
							},
						},
					},
				},
			},
			Footer: &linebot.BoxComponent{
				Type:   linebot.FlexComponentTypeBox,
				Layout: linebot.FlexBoxLayoutTypeVertical,
				Contents: []linebot.FlexComponent{
					&linebot.ButtonComponent{
						Type:  linebot.FlexComponentTypeButton,
						Style: linebot.FlexButtonStyleTypePrimary,
						Color: "#905c44",
						Action: &linebot.URIAction{
							Label: "配信を見る",
							URI:   env.url,
						},
					},
				},
			},
		},
	)

	_, err = client.BroadcastMessage(message).Do()

	if err != nil {
		return
	}

	fmt.Println("配信中！通知しました：" + live.Title)

	return
}

func HandleRequest(ctx context.Context) (string, err error) {
	env, err := getEnv()
	if err != nil {
		fmt.Println(err)
		return
	}

	token, err := getToken(env)
	if err != nil {
		fmt.Println(err)
		return
	}

	channel, err := getChannel(env, token)
	if err != nil {
		fmt.Println(err)
		return
	}

	live, err := getLive(env, token, channel)
	if err != nil {
		fmt.Println(err)
		return
	}

	liveTime, err := getOldLiveTime(env, live)
	if err != nil {
		fmt.Println(err)
		return
	}

	err = sendMessage(env, live, liveTime)
	if err != nil {
		fmt.Println(err)
		return
	}

	return
}

func main() {
	if os.Getenv("APP_ENV") == "production" {
		lambda.Start(HandleRequest)
	} else {
		HandleRequest(nil)
	}
}
