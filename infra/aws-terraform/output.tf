output "owtf_url" {
  value       = aws_lb.alb.dns_name
  description = "This provides Public DNS of the ALB"
}