def absolute_url(base, url):
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        return base + url
    return base + "/" + url
