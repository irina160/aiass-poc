/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
    theme: {
        container: {
            center: true,
            padding: "2rem",
            screens: {
                "2xl": "1400px"
            }
        },
        extend: {
            colors: {
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))"
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))"
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))"
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))"
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))"
                },
                popover: {
                    DEFAULT: "hsl(var(--popover))",
                    foreground: "hsl(var(--popover-foreground))"
                },
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))"
                }
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)"
            },
            keyframes: {
                "accordion-down": {
                    from: { maxHeight: 0 },
                    to: { maxHeight: 335 }
                },
                "accordion-up": {
                    from: { maxHeight: 335 },
                    to: { maxHeight: 0 }
                },
                linearprogress: {
                    "0%": { width: "50%" },
                    "50%": { width: "60%", transform: "translate(40vw, 0)" },
                    "51%": { width: "40%", transform: "translate(0)" },
                    "100%": { width: "10%", transform: "translate(90vw, 0)" }
                },
                spinner: {
                    to: { transform: "rotate(360deg)" }
                },
                "panel-open": {
                    from: { maxWidth: 0, opacity: 0 },
                    to: { maxWidth: 300, opacity: 1 }
                },
                "panel-close": {
                    from: { maxWidth: 300, opacity: 1 },
                    to: { maxWidth: 0, opacity: 0 }
                }
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
                linearprogress: "linearprogress 2s linear infinite",
                spinner: "spinner 0.6s linear infinite",
                "panel-open": "panel-open 1s ease-in",
                "panel-close": "panel-close 1s ease-out"
            },
            backgroundImage: {
                "startpage-background": "url('@assets/kpmg_gen_ai.jpg')" //landing-text-tiles-column-bg-1.jpg')"
            },
            width: {
                "screen-d": ["100vw", "100svw"]
            },
            height: {
                "screen-d": ["100vh", "100svh"],
                inherit: "inherit"
            },
            gridTemplateColumns: {
                dynamic_250: "repeat(auto-fit, minmax(250px, 1fr))",
                dynamic_250_300: "repeat(auto-fit, minmax(250px, 300px))"
            },
            fontFamily: {
                KPMGBold: ["KPMG Bold"],
                KPMGBoldItalic: ["KPMG Bold Italic"],
                KPMGExtralight: ["KPMG Extralight"],
                KPMGExtralightItalic: ["KPMG Extralight Italic"],
                KPMGLight: ["KPMG Light"]
            },
            boxShadow: {
                custom: "0px 8px 16px hsl(var(--accent)), 0px 0px 2px hsl(var(--accent))"
            }
        }
    },
    plugins: [require("tailwindcss-animate")]
};
