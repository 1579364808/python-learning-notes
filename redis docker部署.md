**第一步：拉取 Redis 镜像**

请打开你的终端（Terminal）或命令行（CMD/PowerShell），输入以下命令并回车：

```bash
docker pull redis
```

这个命令会从 Docker Hub 下载官方最新的 Redis 镜像。

**第二步：启动 Redis 容器**

我们将启动一个 Redis 容器，并设置好**端口映射**和**访问密码**。

请在终端执行以下命令（你可以把 `你的密码` 替换成你想设置的真实密码，比如 `123456`）：

```bash
docker run --name my-redis -p 6379:6379 -d redis redis-server --requirepass "你的密码"
```

**命令解释：**
*   `--name my-redis`: 给这个容器起个名字叫 `my-redis`，方便后续管理。
*   `-p 6379:6379`: 把容器里的 6379 端口映射到你电脑的 6379 端口。
*   `-d`: 在后台静默运行。
*   `redis-server --requirepass "..."`: 启动 Redis 服务并设置密码。

**第三步：检查容器运行状态**

我们需要确认 Redis 容器是否已经成功启动并且正在运行。

请在终端执行：

```bash
docker ps
```

**查看结果：**
你应该能看到一行包含 `my-redis` 的记录，且状态（STATUS）显示为 `Up`（例如 `Up 5 seconds`）。

*   如果看不到 `my-redis`，请尝试运行 `docker ps -a` 查看是否有报错退出的容器。

**第四步：进入容器进行测试**

现在我们进入容器内部，使用 `redis-cli` 工具来测试一下数据库是否正常工作。

1.  **进入 Redis 命令行：**
    请执行：
    ```bash
    docker exec -it my-redis redis-cli
    ```
    此时你的命令提示符应该会变成 `127.0.0.1:6379>`。

2.  **验证密码：**
    输入以下命令（替换为你第二步设置的密码）：
    ```bash
    auth "你的密码"
    ```
    如果密码正确，它会返回 `OK`。

3.  **简单测试：**
    输入：
    ```bash
    set mykey "Hello Docker"
    get mykey
    ```
    如果看到输出 `"Hello Docker"`，说明部署完全成功！

4.  **退出：**
    输入 `exit` 退出 Redis 命令行。

