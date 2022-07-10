terraform {
  required_providers {
    mongodbatlas = {
      source = "mongodb/mongodbatlas"
      version = "1.4.2"
    }
  }
}

provider "mongodbatlas" {}

variable "MONGODB_ORG_ID" {} 
variable "MONGODB_API_KEY" {} 

resource "mongodbatlas_project" "jrb" {
  name   = "jrb"
  org_id = var.MONGODB_ORG_ID

  api_keys {
    api_key_id = var.MONGODB_API_KEY
    role_names = [
      "GROUP_OWNER",
    ]
  }

  is_collect_database_specifics_statistics_enabled = true
  is_data_explorer_enabled                         = true
  is_performance_advisor_enabled                   = true
  is_realtime_performance_panel_enabled            = true
  is_schema_advisor_enabled                        = true
}

resource "mongodbatlas_cluster" "jrb" {
    name = "jrb"
    project_id = mongodbatlas_project.jrb.id
    provider_instance_size_name = "M0"
    provider_name = "TENANT"
    auto_scaling_compute_enabled = false
    auto_scaling_compute_scale_down_enabled = false
    auto_scaling_disk_gb_enabled = null
    backing_provider_name = "AWS"
    cloud_backup = false
    cluster_type = "REPLICASET"
    disk_size_gb = 0.5
    encryption_at_rest_provider = "NONE"
    mongo_db_major_version = "5.0"
    pit_enabled = false
    provider_region_name = "AP_NORTHEAST_1"
    replication_factor = 3
    replication_specs {
        regions_config {
            analytics_nodes = 0
            electable_nodes = 3
            priority        = 7
            read_only_nodes = 0
            region_name     = "AP_NORTHEAST_1"
        }
        num_shards = 1
        zone_name = "Zone 1"
    }
}