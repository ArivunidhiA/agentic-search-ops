# ==============================================================================
# CLOUDFRONT ORIGIN ACCESS CONTROL
# ==============================================================================

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_prefix}-kb-frontend-oac"
  description                       = "OAC for Agentic Search Ops frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ==============================================================================
# CLOUDFRONT DISTRIBUTION
# ==============================================================================

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100" # US, Canada, Europe (cheapest)
  comment             = "Agentic Search Ops Frontend"

  # S3 Origin
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.frontend.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # Default cache behavior
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Cache settings
    min_ttl     = 0
    default_ttl = 3600      # 1 hour
    max_ttl     = 86400     # 24 hours

    forwarded_values {
      query_string = false
      
      cookies {
        forward = "none"
      }
    }
  }

  # Cache behavior for static assets (JS, CSS, images)
  ordered_cache_behavior {
    path_pattern           = "/assets/*"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    min_ttl     = 0
    default_ttl = 86400     # 24 hours
    max_ttl     = 31536000  # 1 year

    forwarded_values {
      query_string = false
      
      cookies {
        forward = "none"
      }
    }
  }

  # SPA routing - redirect 404s to index.html
  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 300
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 300
  }

  # Geo restrictions (none)
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL certificate (using CloudFront default)
  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  tags = {
    Name = "${var.project_prefix}-kb-frontend-cdn"
  }

  # Wait for S3 bucket policy to be ready
  depends_on = [aws_s3_bucket_policy.frontend]
}

# ==============================================================================
# CLOUDFRONT CACHE INVALIDATION (for deployments)
# ==============================================================================

# Note: Cache invalidation is done manually via deploy script:
# aws cloudfront create-invalidation --distribution-id ${distribution_id} --paths "/*"
