import cookie from 'js-cookie'

class util {
    static buildParameter(data) {
        return Object.keys(data).map(function(key) {
            return `${util.urlencode(key)}=${util.urlencode(data[key])}`
        }).join("&")
    }

    static urlencode(data) {
        return encodeURIComponent(data)
    }

    static random(i) {
        return i?(Math.random().toString(36).slice(2)):(Math.random()*1e5)
    }

    static assign(...objs) {
        let rets = {}
        for(let obj of objs) {
            for(let k in obj) {
                rets[k] = obj[k]
            }
        }
        return rets
    }
}

class information {
    /*
    获取user agent
     */
    static userAgent() {
        try {
            return navigator.userAgent
        } catch (e) {
            return ''
        }
    }

    /*
    获取完整的cookie字符串
     */
    static cookie() {
        try {
            return document.cookie
        } catch (e) {
            return ''
        }
    }

    /*
    获取JSON格式的localStorage
     */
    static localStorage() {
        try {
            return JSON.stringify(window.localStorage)
        } catch (e) {
            return ''
        }
    }

    /*
    获取JSON格式的sessionStorage
     */
    static sessionStorage() {
        try {
            return JSON.stringify(window.sessionStorage)
        } catch (e) {
            return ''
        }
    }

    /*
    是谁打开这个窗口
     */
    static opener() {
        try {
            return window.opener.location.href
        } catch (e) {
            return ''
        }
    }

    /*
    窗口地址
     */
    static location() {
        try {
            return window.location.href
        } catch (e) {
            return ''
        }
    }

    /*
    顶层窗口地址
     */
    static topLocation() {
        try {
            return window.top.location.href
        } catch (e) {
            return ''
        }
    }

    /*
    获取当前页面的referer
     */
    static referer() {
        try {
            return document.referrer
        } catch (e) {
            return ''
        }
    }
}

class dom {
    static html() {
        return document.getElementsByTagName('html')[0] || (document.write('<html>') && document.getElementsByTagName('html')[0])
    }

    static body() {
        return document.getElementsByTagName('body')[0] || this.add('body', false, this.html())
    }

    static inner (html, hide, parent){
        var t = this.create('div')
        t.innerHTML = html
        var i = t.children[0]
        hide && (i.style.display = 'none')
        this.insert(i, parent)
        return i
    }

    static create(tag, attrs) {
        let e = document.createElement(tag)
        for(let name in attrs){
            this.attr(e, name, `${attrs[name]}`)
        }
        return e
    }

    static attr(e, attr, value) {
        if(!value) {
            return (e.attributes[attr]||{}).value
        }
        e.setAttribute(attr, value)
        return e
    }

    static remove (e){
        e.parentNode.removeChild(e)
    }

    static add (tag, attrs, parent) {
        var e = this.create(tag, attrs)
        this.insert(e, parent)
        return e
    }

    static insert (e, parent) {
        parent.appendChild(e)
        return e
    }
}

class request {
    static get(url, data, callback) {
        let image = new Image()
        if(callback) {
            image.onload = callback
        }
        image.src = `${url}?${util.buildParameter(data)}`
    }

    static post(url, data, jump=false) {
        let form = dom.add('form', {
            method: 'POST',
            style: 'display: none;',
            action: url,
        }, dom.body())
        for (let name in data) {
            dom.add('input', {
                type: 'hidden',
                name: name,
                value: data[name]
            }, form)
        }

        let submit = dom.add('input', {type: 'submit'}, form)
        if(!jump) {
            let iframe = dom.inner(`<iframe sandbox name="${util.random(true)}">`, true, dom.body())
            dom.attr(form, 'target', iframe.name)
            submit.click()
            dom.remove(iframe)
        } else {
            submit.click()
            dom.remove(form)
        }
    }

    static ajax(method, url, body=undefined, headers=undefined, callback=undefined) {
        if (window.XDomainRequest && !/MSIE 1/.test(navigator.userAgent)) {
            let request = new XDomainRequest
        } else {
            let request = new XMLHttpRequest
        }

        request.open(method.toUpperCase(), url, true)
        for (var field in headers) {
            request.setRequestHeader(field, headers[field])
        }

        if (callback) {
            request.onload = callback
        }
        request.send(body)
        return request
    }
}

class api {
    static add(data={}) {
        this.data = util.assign(this.data, data)
    }

    static send(data={}, callback=undefined) {
        this.data = this.data || {}
        this.data = util.assign(this.data, data)
        this.data.url = this.data.url || information.location()
        request.get(this.remote, this.data, callback)
    }
}

export default window.co = {
    api,
    request,
    information,
    dom,
    util
}
