let currentUser = null;
let fetchPromise = null;


// caching to avoid redundant api calls
export async function getCurrentUser() {
  if (currentUser) {
    return currentUser;
  }

  // Return in-progress fetch to prevent duplicate API calls
  // if fetch is already in line we will retuen this promise instead of another request
  // as multple page geeting current user
  if (fetchPromise) {
    return fetchPromise;
  }

  const token = localStorage.getItem("access_token");
  if (!token) {
    return null;
  }


  // is checking token is valid
  fetchPromise = (async () => {
    try {
      const response = await fetch("/api/users/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        currentUser = await response.json();
        return currentUser;
      }

      localStorage.removeItem("access_token");
      return null;
    } catch (error) {
      console.error("Error fetching current user:", error);
      return null;
    } finally {
      fetchPromise = null;
    }
  })();

  return fetchPromise;
}

export function logout() {
  localStorage.removeItem("access_token");
  currentUser = null;
  window.location.href = "/";
}

export function getToken() {
  return localStorage.getItem("access_token");
}

export function setToken(token) {
  localStorage.setItem("access_token", token);
}

export function clearUserCache() {
  currentUser = null;
}  