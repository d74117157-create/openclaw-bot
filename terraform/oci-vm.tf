variable "tenancy_ocid" {}
variable "compartment_ocid" {}
variable "region" { default = "us-ashburn-1" }
variable "ssh_public_key" {}
variable "vm_shape" { default = "VM.Standard.A1.Flex" }
variable "ocpus" { default = 1 }
variable "memory_in_gbs" { default = 6 }

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  region           = var.region
}

# Get availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# Create VCN
resource "oci_core_vcn" "openclaw_vcn" {
  compartment_id = var.compartment_ocid
  cidr_block     = "10.0.0.0/16"
  display_name   = "openclaw-vcn"
  dns_label      = "openclaw"
}

# Internet Gateway
resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-igw"
}

# Route Table
resource "oci_core_route_table" "rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.igw.id
  }
}

# Security List — allow SSH, HTTP, HTTPS
resource "oci_core_security_list" "sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-sl"

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 8000
      max = 8000
    }
  }
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# Subnet
resource "oci_core_subnet" "subnet" {
  compartment_id      = var.compartment_ocid
  vcn_id              = oci_core_vcn.openclaw_vcn.id
  cidr_block          = "10.0.1.0/24"
  display_name        = "openclaw-subnet"
  dns_label           = "subnet"
  route_table_id      = oci_core_route_table.rt.id
  security_list_ids   = [oci_core_security_list.sl.id]
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
}

# Get latest Oracle Linux image
data "oci_core_images" "ol8" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.vm_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# VM Instance
resource "oci_core_instance" "openclaw_worker" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_ocid
  display_name        = "openclaw-worker"
  shape               = var.vm_shape

  shape_config {
    ocpus         = var.ocpus
    memory_in_gbs = var.memory_in_gbs
  }

  source_details {
    source_type = "image"
    image_id    = data.oci_core_images.ol8.images[0].id
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.subnet.id
    display_name     = "openclaw-vnic"
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(templatefile("${path.module}/cloud-init.yaml", {}))
  }
}

output "public_ip" {
  value = oci_core_instance.openclaw_worker.public_ip
}

output "instance_id" {
  value = oci_core_instance.openclaw_worker.id
}
