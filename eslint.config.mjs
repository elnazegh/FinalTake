export default [
  {
    files: ["frontend/js/**/*.js"],
    languageOptions: {
      globals: {
        alert: "readonly",
        console: "readonly",
        document: "readonly",
        fetch: "readonly",
        URLSearchParams: "readonly",
        window: "readonly"
      }
    },
    rules: {
      "no-constant-condition": "error",
      "no-dupe-keys": "error",
      "no-undef": "error",
      "no-unreachable": "error",
      "no-unused-vars": ["error", { caughtErrors: "none" }],
      "valid-typeof": "error"
    }
  },
  {
    files: ["frontend/js/rating-ui.js"],
    rules: {
      // The inline script in rating-demo.html consumes this global function.
      "no-unused-vars": [
        "error",
        {
          caughtErrors: "none",
          varsIgnorePattern: "^createRatingSelector$"
        }
      ]
    }
  }
];
