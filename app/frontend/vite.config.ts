import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import svgr from "vite-plugin-svgr";
import tailwindcss from "tailwindcss";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react(), svgr(), tailwindcss()],
    build: {
        outDir: "../backend/static",
        emptyOutDir: true,
        sourcemap: true,
        rollupOptions: {
            output: {
                manualChunks: id => {
                    if (id.includes("@fluentui/react-icons")) {
                        return "fluentui-icons";
                    } else if (id.includes("@fluentui/react")) {
                        return "fluentui-react";
                    } else if (id.includes("node_modules")) {
                        return "vendor";
                    }
                }
            }
        }
    },
    /**
     * TODO: Change api Endpoints in backend
     */
    server: {
        proxy: {
            "/api": {
                target: "http://localhost:50505"
            }
        }
    },
    resolve: {
        alias: {
            "@components": path.resolve(__dirname, "src/components/"),
            "@pages": path.resolve(__dirname, "src/pages"),
            "@assets": path.resolve(__dirname, "src/assets"),
            "@hooks": path.resolve(__dirname, "src/hooks"),
            "@lib": path.resolve(__dirname, "src/lib")
        }
    }
});
