**Archived: 请使用2.0版本 <https://phith0n.github.io/conote-docs/>，CoNote 1.0版本不再维护。**


# CoNote 综合安全测试平台（社区版）

CoNote是一个内部使用的工作台，它会让我们的安全测试过程变得非常方便，于2021年12月推出社区版。

使用说明：<https://phithon.gitbooks.io/conote/content/>

演示视频：

[![conote](img/2.png)](https://www.youtube.com/watch?v=WqbjJ8NISys)

![](img/3.png)

搭建文档尚不完善，尽情期待，有能力的同学可以先自行研究。

## 全局配置与环境变量

conote使用.env来配置环境变量，我们需要先将文件`.env.default`复制成`.env`。

具体值的意义，请参考conf/settings.py以及conf/settings_deploy.py。

## 主域名

conote平台需要一个主域名，如`note.leavesongs.com`，用户可以通过这个域名访问管理页面。

主域名不用在配置文件里配置。

## 子域名

每个用户将被分配一个子域名，这个域名用于：

1. 记录Web日志
2. 记录DNS日志
3. 存放并访问用户笔记

在配置文件中配置如下选项，指定根域名（每个用户分配到的子域名将是`xxxx.2m1.pw`）：

```python
O_SERVER_DOMAIN = '2m1.pw'
```

这个域名如何配置解析，在下一节进行说明。

## DNS 配置

因为要记录DNS日志，所以我们需要将conote配置成一个DNS服务器。

首先，选择两个域名`ns1.leavesongs.com`、`ns2.leavesongs.com`（随意即可，无要求），A记录指向conote服务器IP。

然后，在配置文件中增加如下选项：

```python
O_NS1_DOMAIN = 'ns1.leavesongs.com'
O_NS2_DOMAIN = 'ns2.leavesongs.com'
O_SERVER_IP = '45.32.43.49'
O_ADDITION_ZONE = ''
```

然后，在`O_SERVER_DOMAIN`域名（也就是`2m1.pw`）的注册商处，配置DNS服务器为`ns1.leavesongs.com`和`ns2.leavesongs.com`。

`O_ADDITION_ZONE`中可以配置一些额外的DNS区域，比如MX记录等。

## 配置用户自定义DNS域名

conote可以允许用户配置自定义的DNS记录，用于测试Rebind漏洞。

选择一个`O_SERVER_DOMAIN`的子域名（不要和用户的子域名重复），如`s.2m1.pw`。增加如下配置：

```python
O_REBIND_DOMAIN = 's.2m1.pw'
```

不再需要额外配置，因为conote的DNS服务器会接管这个域名。

## 配置短域名

conote支持短域名模块，我们可以注册一个短域名，如`mhz.pw`，然后增加如下配置：

```python
O_SHORT_DOMAIN = 'mhz.pw'
```

然后需要在域名解析商处将这个域名指向conote的IP地址。

当然，也可以配置为`O_SERVER_DOMAIN`的另一个子域名，如`a.2m1.pw`。但这时候，我们就需要修改`O_ADDITION_ZONE`，为这个子域名添加一个A记录，因为此时即conote充当域名解析商的角色。

## 配置XSS平台域名

conote支持xss平台，除了名字不同，配置同上一节：

```python
O_XSS_DOMAIN = 'tj.2m1.pw'
```

## 配置第三方登录

CoNote现在使用的是第三方登录，如果要对接自己的OAuth平台，我们可以略微修改代码。

首先在.env中修改OAuth的配置项：

```
CLIENT_ID=xxxx
CLIENT_SECRET=xxxx
CALLBACK_URL=http://note.leavesongs.com/auth/callback/
# 将callback_url中的example.com修改成conote平台主域名即可，path不要修改。
```

然后在`app/ucenter/views.py`中，修改如下三个url：

```python
authorization_base_url = 'https://auth.tricking.io/o/authorize/'
token_url = 'https://auth.tricking.io/o/token/'
profile_url = 'https://auth.tricking.io/api/profile/'
```

第一个是获取code的url，第二个是用code兑换access_token的url，第三个是获取用户信息的url。

然后修改一下同文件中的RegisterView类：

```python
class RegisterView(generic.CreateView):
    model = User
    fields = [
        'username',
        'email'
    ]
    template_name = 'registration/register.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            session = OAuth2Session(client_id, token=request.session['oauth_token'])
            self.user_data = session.get(profile_url).json()
        except BaseException as e:
            return render(request, '500.html', context=dict(errors=str(e)))

        user = User.objects.filter(auth_id=self.user_data['auth_id']).first()
        if user:
            self.login(user)
            return redirect(resolve_url(settings.LOGIN_REDIRECT_URL))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return dict(
            username=self.user_data['username'],
            email=self.user_data['email']
        )

    def login(self, user):
        auth_login(self.request, user)
        self.request.session.pop('oauth_token', None)
        self.request.session.pop('oauth_state', None)

    @transaction.atomic
    def form_valid(self, form):
        form.instance.set_unusable_password()
        form.instance.auth_id = self.user_data['auth_id']
        user = form.save()
        self.login(user)
        return redirect(resolve_url(settings.LOGIN_REDIRECT_URL))
    # ...
```

其中`self.user_data`是获取到的用户信息，修改成你的平台提供的信息即可。

## 配置Docker

拉取新的镜像：

```
docker pull php:7.2-fpm-alpine
docker pull php:5.6-fpm-alpine
```

如果希望限制容器内tmp文件夹大小，请先创建一个文件系统，步骤如下：

```bash
# 创建一个大小为64M的文件
dd if=/dev/zero bs=1024 count=64000 of=/usr/local/tmpfile

# 对文件进行格式化
mkfs.ext4 /usr/local/tmpfile

# 建立目录
mkdir /data/tmp

# 修改/etc/fstab
vim /etc/fstab
# /usr/local/tmpfile /data/tmp ext4 rw,user,auto,noexec 0 0

# 或手工挂载
mount -o loop /usr/local/tmpfile /data/tmp
```

然后，配置settings.py：

```python
SANDBOX_ROOT = os.path.join(BASE_DIR, 'media', 'sandbox')
DOCKER_CONFIG = {
    'php-5.6': {
        'image': 'php:5.6-fpm-alpine',
        'container_name': 'conote_php56',
        'network_name': 'network_01',
        'subnet': '10.233.101.0/24',
        'gateway': '10.233.101.254',
        'ip': '10.233.101.10',
        'tmp': '/data/tmp/php56'
    },
    'php-7.2': {
        'image': 'php:7.2-fpm-alpine',
        'container_name': 'conote_php72',
        'network_name': 'network_02',
        'subnet': '10.233.102.0/24',
        'gateway': '10.233.102.254',
        'ip': '10.233.102.10',
        'tmp': '/data/tmp/php72'
    }
}
```

Docker启动后，还需要将tmp目录权限修改为0777。

如果不用限制/tmp目录的大小，则无需上述操作，且settings中tmp的值为`None`。

### 下载gvisor

conote利用[gvisor](https://github.com/google/gvisor)来控制沙箱，所以需要下载gvisor的二进制文件并配置docker：

下载二进制文件:`wget https://storage.googleapis.com/gvisor/releases/nightly/latest/runsc -O /usr/local/bin/runsc`，并给其添加可执行权限`chmod +x /usr/local/bin/runsc`，然后修改docker配置文件`/etc/docker/daemon.json`（如果不存在则创建之）：

```
{
    "runtimes": {
        "runsc": {
            "path": "/usr/local/bin/runsc"
        }
    }
}
```

最后重启docker即可。

## 配置匿名邮箱与SMTP模块

在DNS服务商处（或conote的DNS配置处），设置MX记录指向服务器IP。

```python
1m6.win.         IN      MX      5 note.leavesongs.com.
```

然后在settings中设置：

```python
O_MAIL_DOMAIN = '1m6.win'
```

用`./manage.py mailserver`启动smtp服务器，将监听0.0.0.0:25。

## 运行conote

conote分为4部分：

1. web端
2. dns服务器
3. 后台任务
4. smtp服务器

所以需要分成4个服务运行。systemd文件如下：

```
# Conote
[Unit]
Description=Conote web application
After=network.target

[Service]
PIDFile=/run/gunicorn/conote.pid
RuntimeDirectory=gunicorn
User=root
Group=root
WorkingDirectory=/home/conote
Restart=always
ExecStart=/bin/bash /home/conote/conote.sh --pid /run/gunicorn/conote.pid
ExecStop=/bin/kill -s TERM $MAINPID

[Install]
WantedBy=multi-user.target
```

```
# dns server
[Unit]
Description=Conote dns application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/home/conote
Restart=always
ExecStart=/home/conote/env/bin/python manage.py dnsserver

[Install]
WantedBy=multi-user.target
```

```
# huey
[Unit]
Description=Conote huey background tasks
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/home/conote
Restart=always
ExecStart=/home/conote/env/bin/python manage.py run_huey

[Install]
WantedBy=multi-user.target
```

```
# smtpd
[Unit]
Description=Conote email server
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/home/conote
Restart=always
ExecStart=/home/conote/env/bin/python manage.py mailserver

[Install]
WantedBy=multi-user.target
```
