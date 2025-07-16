const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    client: {
      overlay: {
        warnings: false,
        errors: true,
        runtimeErrors: (error) => {
          if (error.message.includes('ResizeObserver loop completed with undelivered notifications')) {
            // Returning false hides the error from the overlay.
            return false;
          }
          // Show all other errors.
          return true;
        },
      },
    },
  },
}); 