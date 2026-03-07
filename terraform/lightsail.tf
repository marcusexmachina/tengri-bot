resource "aws_lightsail_key_pair" "tengri" {
  name = "${var.project_name}-key"
}

resource "aws_lightsail_instance" "tengri" {
  name              = var.project_name
  availability_zone = "${var.aws_region}a"
  blueprint_id      = var.lightsail_blueprint_id
  bundle_id         = var.lightsail_bundle_id
  key_pair_name    = aws_lightsail_key_pair.tengri.name

  tags = {
    Name = var.project_name
  }
}

resource "aws_lightsail_static_ip" "tengri" {
  name = "${var.project_name}-ip"
}

resource "aws_lightsail_static_ip_attachment" "tengri" {
  static_ip_name = aws_lightsail_static_ip.tengri.name
  instance_name  = aws_lightsail_instance.tengri.name
}
