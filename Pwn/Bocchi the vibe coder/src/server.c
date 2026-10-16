#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>

void send_all(const char *buf, size_t n) {
    size_t off = 0;
    while (off < n) {
        ssize_t w = write(1, buf + off, n - off);
        if (w <= 0) _exit(0);
        off += (size_t)w;
    }
}

void http_header(int code, const char *status, size_t len) {
    char hdr[160];
    int n = snprintf(hdr, sizeof(hdr),
        "HTTP/1.0 %d %s\r\nServer: bocchi/0.1\r\nContent-Length: %zu\r\n\r\n",
        code, status, len);
    send_all(hdr, (size_t)n);
}

void serve_file(const char *path) {
    const char *rel = path;
    while (*rel == '/') rel++;
    if (*rel == 0) rel = "index.html";
    if (strstr(rel, "..")) {
        const char *m = "nope\n";
        http_header(403, "Forbidden", strlen(m));
        send_all(m, strlen(m));
        return;
    }
    int fd = open(rel, O_RDONLY);
    if (fd < 0) {
        const char *m = "not found\n";
        http_header(404, "Not Found", strlen(m));
        send_all(m, strlen(m));
        return;
    }
    off_t total = lseek(fd, 0, SEEK_END);
    lseek(fd, 0, SEEK_SET);
    if (total < 0) total = 0;
    http_header(200, "OK", (size_t)total);
    char body[4096];
    ssize_t r;
    while ((r = read(fd, body, sizeof(body))) > 0)
        send_all(body, (size_t)r);
    close(fd);
}

void handle_get(const char *path_tok, size_t path_len) {
    char path[256];
    memcpy(path, path_tok, path_len);
    if (path_len >= sizeof(path)) path_len = sizeof(path) - 1;
    path[path_len] = 0;
    serve_file(path);
}

void handle_bocchi(const char *body, size_t body_len) {
    char buf[64];
    *(void **)buf = stdout;
    if (body_len == 0) {
        http_header(200, "OK", sizeof(buf));
        send_all(buf, sizeof(buf));
        return;
    }
    if (body_len > sizeof(buf)) body_len = sizeof(buf);
    memcpy(buf, body, body_len);
    http_header(200, "OK", body_len);
    send_all(buf, body_len);
}

void handle_request(char *req, size_t n) {
    char *sp1 = memchr(req, ' ', n);
    if (!sp1) return;
    size_t method_len = (size_t)(sp1 - req);
    char *path_start = sp1 + 1;
    size_t rest = n - (size_t)(path_start - req);
    char *sp2 = memchr(path_start, ' ', rest);
    char *nl = memchr(path_start, '\n', rest);
    char *path_end;
    if (sp2 && (!nl || sp2 < nl)) path_end = sp2;
    else if (nl) path_end = nl;
    else path_end = path_start + rest;
    size_t path_len = (size_t)(path_end - path_start);

    if (method_len == 3 && memcmp(req, "GET", 3) == 0) {
        handle_get(path_start, path_len);
    } else if (method_len == 6 && memcmp(req, "BOCCHI", 6) == 0) {
        char *body = memmem(req, n, "\r\n\r\n", 4);
        if (body) handle_bocchi(body + 4, n - (size_t)(body + 4 - req));
        else handle_bocchi(req, 0);
    } else {
        const char *m = "wip, reviens plus tard\n";
        http_header(501, "Not Implemented", strlen(m));
        send_all(m, strlen(m));
    }
}

void decoy(void) {
    puts("CYNNRNIGHTFLAG{IsThisArealFlag?} ");
    for (int i = 0; i < 3; i++)
        puts("🟦🟨🎸😐");
    _exit(0);
}

int main(void) {
    if (getenv("LINES")) decoy();
    char req[8192];
    for (;;) {
        ssize_t n = read(0, req, sizeof(req));
        if (n <= 0) break;
        handle_request(req, (size_t)n);
    }
    return 0;
}
