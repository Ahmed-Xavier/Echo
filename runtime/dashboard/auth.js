(function () {
  const SESSION_KEY = "echo_dashboard_session";
  const LOGIN_PAGE = "login.html";

  const publicPages = ["/login.html", "login.html"];
  const path = window.location.pathname;
  const isLoginPage = publicPages.some((page) => path.endsWith(page));

  function getSession() {
    try {
      return JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    } catch {
      return null;
    }
  }

  function isValidSession(session) {
    if (!session || !session.loggedIn) return false;
    if (!session.expiresAt) return false;
    return Date.now() < Number(session.expiresAt);
  }

  window.EchoAuth = {
    login(username) {
      const now = Date.now();
      const session = {
        loggedIn: true,
        username: username || "Ahmed",
        role: "Operator",
        loginAt: now,
        expiresAt: now + 1000 * 60 * 60 * 12
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
      return session;
    },

    logout() {
      localStorage.removeItem(SESSION_KEY);
      window.location.href = LOGIN_PAGE;
    },

    session: getSession,

    requireLogin() {
      if (!isValidSession(getSession())) {
        window.location.href = LOGIN_PAGE;
      }
    }
  };

  if (!isLoginPage) {
    window.EchoAuth.requireLogin();
  }
})();
