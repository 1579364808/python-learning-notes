## 下载 MySQL 镜像

```
docker pull mysql
```

## 启动 MySQL 容器

```
docker run --name mysql-container -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 -d mysql
```

**命令解释：**
*   `--name`：给容器起个名字
*   `-e MYSQL_ROOT_PASSWORD=123456`：设置管理员（root）密码为 `123456`
*   `-p 3306:3306`：把电脑的 3306 端口连通到容器的 3306 端口
*   `-d`：在后台静默运行，不占用当前终端窗口。

## 确认容器正在运行
```
docker ps
```
**Process Status**

## 进入容器验证连接
```
docker exec -it mysql-container mysql -u root -p
```
## 停止与重启容器
不需要每次都重新创建容器（那样数据会丢失）。平时不用时可以把它关掉，用的时候再开。
```
docker stop mysql-container
```
下次你想再用它时，只需要输入 

```
docker start mysql-container
```

## 删除容器

```
docker rm mysql-container
```