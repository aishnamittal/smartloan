window.onload = () => {
    const token = localStorage.getItem("token");  // Use token from login
  
    const ui = SwaggerUIBundle({
      url: "/openapi.json",
      dom_id: "#swagger-ui",
      presets: [SwaggerUIBundle.presets.apis],
      layout: "BaseLayout",
      requestInterceptor: (req) => {
        if (token) {
          req.headers["Authorization"] = `Bearer ${token}`;
        }
        return req;
      }
    });
  
    window.ui = ui;
  };
  