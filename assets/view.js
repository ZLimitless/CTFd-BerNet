CTFd._internal.challenge.data = undefined

CTFd._internal.challenge.renderer = CTFd.lib.markdown();

CTFd._internal.challenge.preRender = function () {
}

CTFd._internal.challenge.render = function (markdown) {
    return CTFd._internal.challenge.renderer.render(markdown)
}

CTFd._internal.challenge.postRender = function () {
    loadInfo();
}

if ($ === undefined) $ = CTFd.lib.$;

function loadInfo() {
    var challenge_id = $('#challenge-id').val();
    var url = "/api/v1/plugins/ctfd-bernet/container?challenge_id=" + challenge_id;

    var params = {};

    CTFd.fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (window.t !== undefined) {
            clearInterval(window.t);
            window.t = undefined;
        }
        if (response.success) response = response.data;
        else CTFd.ui.ezq.ezAlert({
            title: "Fail",
            body: response.message,
            button: "OK"
        });
        if (response.remaining_time === undefined) {
            $('#bernet-panel').html('<div class="card" style="width: 100%;">' +
                '<div class="card-body">' +
                '<h5 class="card-title">Instance Info</h5>' +
                '<button type="button" class="btn btn-primary card-link" id="bernet-button-boot" ' +
                '        onclick="CTFd._internal.challenge.boot()">' +
                '开启题目' +
                '</button>' +
                '</div>' +
                '</div>');
        }else {
            if (response.Command !== undefined){
                $('#bernet-panel').html(
                `<div class="card" style="width: 100%;">
                    <div class="card-body">
                        <h5 class="card-title">容器信息</h5>
                        <h6 class="card-subtitle mb-2 text-muted" id="bernet-challenge-count-down">
                            Remaining Time: ${response.remaining_time}s
                        </h6>
                        <h5 class="card-text">
                            Pwn Me: <br>${response.Command}
                        </h5>
                        <p id="user-access" class="card-text"></p>
                        <button type="button" class="btn btn-danger card-link" id="bernet-button-destroy"
                                onclick="CTFd._internal.challenge.destroy()">
                            删除容器
                        </button>
                        <button type="button" class="btn btn-success card-link" id="bernet-button-renew"
                                onclick="CTFd._internal.challenge.renew()">
                            续时该容器
                        </button>
                    </div>
                </div>`
            );
            $('#user-access').html(response.user_access);
            }else {
                $('#bernet-panel').html(
                    `<div class="card" style="width: 100%;">
                    <div class="card-body">
                        <h5 class="card-title">容器信息</h5>
                        <h6 class="card-subtitle mb-2 text-muted" id="bernet-challenge-count-down">
                            Remaining Time: ${response.remaining_time}s
                        </h6>
                        <h6 class="card-text">
                            题目地址: ${response.lan_domain}
                        </h6>
                        <h6 class="card-subtitle mb-3 text-muted">
                            <a href="http://${response.lan_domain}" target="_blank" >点击此处跳转到题目</a>
                        </h6>
                        <p id="user-access" class="card-text"></p>
                        <button type="button" class="btn btn-danger card-link" id="bernet-button-destroy"
                                onclick="CTFd._internal.challenge.destroy()">
                            删除容器
                        </button>
                        <button type="button" class="btn btn-success card-link" id="bernet-button-renew"
                                onclick="CTFd._internal.challenge.renew()">
                            续时该容器
                        </button>
                    </div>
                </div>`
                );
                $('#user-access').html(response.user_access);
            }
            function showAuto() {
                const c = $('#bernet-challenge-count-down')[0];
                if (c === undefined) return;
                const origin = c.innerHTML;
                const second = parseInt(origin.split(": ")[1].split('s')[0]) - 1;
                c.innerHTML = '剩余时间: ' + second + 's';
                if (second < 0) {
                    loadInfo();
                }
            }

            window.t = setInterval(showAuto, 1000);
        }
    });
};

CTFd._internal.challenge.destroy = function () {
    var challenge_id = $('#challenge-id').val();
    var url = "/api/v1/plugins/ctfd-bernet/container?challenge_id=" + challenge_id;

    $('#bernet-button-destroy')[0].innerHTML = "Waiting...";
    $('#bernet-button-destroy')[0].disabled = true;

    var params = {};

    CTFd.fetch(url, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            loadInfo();
            CTFd.ui.ezq.ezAlert({
                title: "Success",
                body: "题目环境删除成功",
                button: "OK"
            });
        } else {
            $('#bernet-button-destroy')[0].innerHTML = "删除题目环境";
            $('#bernet-button-destroy')[0].disabled = false;
            CTFd.ui.ezq.ezAlert({
                title: "Fail",
                body: response.message,
                button: "OK"
            });
        }
    });
};

CTFd._internal.challenge.renew = function () {
    var challenge_id = $('#challenge-id').val();
    var url = "/api/v1/plugins/ctfd-bernet/container?challenge_id=" + challenge_id;

    $('#bernet-button-renew')[0].innerHTML = "Waiting...";
    $('#bernet-button-renew')[0].disabled = true;

    var params = {};

    CTFd.fetch(url, {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            loadInfo();
            CTFd.ui.ezq.ezAlert({
                title: "Success",
                body: "题目环境续时成功",
                button: "OK"
            });
        } else {
            $('#bernet-button-renew')[0].innerHTML = "续时题目环境";
            $('#bernet-button-renew')[0].disabled = false;
            CTFd.ui.ezq.ezAlert({
                title: "Fail",
                body: response.message,
                button: "OK"
            });
        }
    });
};

CTFd._internal.challenge.boot = function () {
    var challenge_id = $('#challenge-id').val();
    var url = "/api/v1/plugins/ctfd-bernet/container?challenge_id=" + challenge_id;

    $('#bernet-button-boot')[0].innerHTML = "Waiting...";
    $('#bernet-button-boot')[0].disabled = true;

    var params = {};

    CTFd.fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            loadInfo();
            CTFd.ui.ezq.ezAlert({
                title: "Success",
                body: "题目容器创建成功(一个用户只能运行一个容器)",
                button: "OK"
            });
        } else {
            $('#bernet-button-boot')[0].innerHTML = "开启题目";
            $('#bernet-button-boot')[0].disabled = false;
            CTFd.ui.ezq.ezAlert({
                title: "Fail",
                body: response.message,
                button: "OK"
            });
        }
    });
};


CTFd._internal.challenge.submit = function (preview) {
    var challenge_id = $('#challenge-id').val();
    var submission = $('#challenge-input').val()

    var body = {
        'challenge_id': challenge_id,
        'submission': submission,
    }
    var params = {}
    if (preview)
        params['preview'] = true

    return CTFd.api.post_challenge_attempt(params, body).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response
        }
        return response
    })
};
