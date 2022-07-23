.PHONY: exec build clean rebuild upload log

SERVICE:=terraform
ENTRY_POINT:=/bin/ash

GOARCH:=amd64
GOOS:=linux
ZIP:=upload.zip
BINARY:=jrb
GO_FILE:=main.go

FUNCTION_NAME:=batch_jun_remind

exec:
	@docker-compose exec $(SERVICE) $(ENTRY_POINT)

build: $(ZIP)

$(ZIP): $(BINARY)
	@zip -r $@ $<

$(BINARY): $(GO_FILE)
	@GOARCH=$(GOARCH) GOOS=$(GOOS) go build -o $@ $<

clean:
	@rm -rf jrb upload.zip

rebuild: clean
	$(MAKE) build

upload: $(ZIP)
	@aws lambda update-function-code --function-name $(FUNCTION_NAME) --zip-file fileb://$(ZIP)

log:
	@aws logs tail --follow /aws/lambda/$(FUNCTION_NAME)