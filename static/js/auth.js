(function () {
    const TOKEN_KEY = 'halaltracker-token';
    const ROLE_KEY = 'halaltracker-role';
    const USER_KEY = 'halaltracker-username';

    const AuthManager = {
        getToken() { return localStorage.getItem(TOKEN_KEY); },
        getRole() { return localStorage.getItem(ROLE_KEY); },
        getUsername() { return localStorage.getItem(USER_KEY); },
        isLoggedIn() { return !!this.getToken(); },
        isSuperadmin() { return this.getRole() === 'superadmin'; },

        setSession(token, role, username) {
            localStorage.setItem(TOKEN_KEY, token);
            localStorage.setItem(ROLE_KEY, role);
            localStorage.setItem(USER_KEY, username);
        },

        logout() {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(ROLE_KEY);
            localStorage.removeItem(USER_KEY);
            window.location.href = '/login.html';
        },
    };

    window.AuthManager = AuthManager;

    const isLoginPage = window.location.pathname.endsWith('/login.html');

    // Login sahifasidan boshqa har qanday sahifa himoyalangan —
    // token bo'lmasa darhol login sahifasiga qaytaramiz.
    if (!isLoginPage && !AuthManager.isLoggedIn()) {
        window.location.href = '/login.html';
        return;
    }

    // app.js va boshqa fayllarga tegmasdan, barcha /api so'rovlariga
    // avtomatik ravishda Authorization headerini qo'shib yuboramiz.
    const _originalFetch = window.fetch.bind(window);
    window.fetch = function (input, init = {}) {
        const url = typeof input === 'string' ? input : input.url;
        const isApiCall = url.startsWith('/api');

        if (isApiCall) {
            const token = AuthManager.getToken();
            init = {
                ...init,
                headers: {
                    ...(init.headers || {}),
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
            };
        }

        return _originalFetch(input, init).then((res) => {
            if (res.status === 401 && isApiCall) {
                AuthManager.logout();
            }
            return res;
        });
    };
})();

