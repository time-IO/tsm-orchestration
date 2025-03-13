group "default" {
    targets = [
        "init"
    ]
}

target "init" {
    context    = "init"
    dockerfile = "Dockerfile"
    tags       = ["test/init:test"]
    args = {
        UID               = "1000"
        GID               = "1000"
        BASE_IMAGE_TAG    = env("INIT_ALPINE_BASE_IMAGE_TAG")
    }
}

