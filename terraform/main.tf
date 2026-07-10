terraform {
  required_providers {
    oci = { source = "oracle/oci", version = "~> 5.0" }
  }
}
provider "oci" { region = var.region }

resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "private_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "${path.module}/oci_vm_key"
  file_permission = "0600"
}

resource "local_file" "public_key" {
  content         = tls_private_key.ssh.public_key_openssh
  filename        = "${path.module}/oci_vm_key.pub"
  file_permission = "0644"
}

resource "oci_core_vcn" "openclaw_vcn" {
  compartment_id = var.compartment_id
  cidr_block     = "10.0.0.0/16"
  display_name   = "openclaw-vcn"
  dns_label      = "openclawvcn"
}

resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-igw"
}

resource "oci_core_route_table" "public_rt" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-public-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.igw.id
  }
}

resource "oci_core_subnet" "public_subnet" {
  compartment_id      = var.compartment_id
  vcn_id              = oci_core_vcn.openclaw_vcn.id
  cidr_block          = "10.0.1.0/24"
  display_name        = "openclaw-public-subnet"
  dns_label           = "publicsub"
  route_table_id      = oci_core_route_table.public_rt.id
  security_list_ids   = [oci_core_security_list.openclaw_sl.id]
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
}

resource "oci_core_security_list" "openclaw_sl" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.openclaw_vcn.id
  display_name   = "openclaw-security-list"
  ingress_security_rules {
    protocol = "6"; source = "0.0.0.0/0"; description = "SSH"
    tcp_options { min = 22; max = 22 }
  }
  ingress_security_rules {
    protocol = "6"; source = "0.0.0.0/0"; description = "HTTP"
    tcp_options { min = 80; max = 80 }
  }
  ingress_security_rules {
    protocol = "6"; source = "0.0.0.0/0"; description = "HTTPS"
    tcp_options { min = 443; max = 443 }
  }
  ingress_security_rules {
    protocol = "6"; source = "0.0.0.0/0"; description = "FastAPI"
    tcp_options { min = 8000; max = 8000 }
  }
  egress_security_rules {
    protocol = "all"; destination = "0.0.0.0/0"
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_id
  operating_system           = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = var.vm_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "openclaw_vm" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_id
  display_name        = "openclaw-vm"
  shape               = var.vm_shape
  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu.images[0].id
  }
  create_vnic_details {
    subnet_id        = oci_core_subnet.public_subnet.id
    assign_public_ip = true
  }
  metadata = {
    ssh_authorized_keys = tls_private_key.ssh.public_key_openssh
  }
  shape_config {
    ocpus         = 1
    memory_in_gbs = 1
  }
}

output "vm_public_ip" {
  value       = oci_core_instance.openclaw_vm.public_ip
  description = "Public IP of the OpenClaw Oracle VM"
}

output "ssh_private_key_path" {
  value       = local_file.private_key.filename
  description = "Path to generated SSH private key"
}

output "ssh_command" {
  value = "ssh -i ${local_file.private_key.filename} ubuntu@${oci_core_instance.openclaw_vm.public_ip}"
}

output "github_secret_value" {
  value     = tls_private_key.ssh.private_key_pem
  sensitive = true
}
