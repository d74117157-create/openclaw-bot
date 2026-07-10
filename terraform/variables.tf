variable "region" {
  description = "OCI region"
  type        = string
  default     = "us-ashburn-1"
}

variable "compartment_id" {
  description = "OCI compartment OCID"
  type        = string
}

variable "vm_shape" {
  description = "VM shape (VM.Standard.E2.1.Micro is Always Free)"
  type        = string
  default     = "VM.Standard.E2.1.Micro"
}
