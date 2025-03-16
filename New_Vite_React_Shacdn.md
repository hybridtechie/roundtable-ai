# Instructions to Set Up a React Project with Vite, Tailwind CSS, and shadcn/ui

## Step 1: Initialize a React Project with Vite

Vite is a fast and lightweight build tool, ideal for React applications.

Run the following command in your terminal to create a new React project:

```bash
npm create vite@latest my-shadcn-app -- --template react-ts
```

Replace `my-shadcn-app` with your preferred project name.

Use `--template react` for JavaScript instead of TypeScript.

Navigate into your new project directory:

```bash
cd my-shadcn-app
```

Install dependencies:

```bash 
npm install
```

Start the development server to verify setup:

```bash
npm run dev
```

## Step 2: Install and Configure Tailwind CSS

Install Tailwind CSS and dependencies:

```bash
npm install tailwindcss @tailwindcss/vite
```


### Configure Vite Plugin

Update `vite.config.ts`:

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
```

Import Tailwind CSS
Replace everything in src/index.css with:

```@import "tailwindcss";```

Configure Tailwind to scan your files
Create or update tailwind.config.js:

```bash
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

Test Tailwind CSS integration
Update src/App.tsx:

```javascript
import React from 'react';

function App() {
  return (
    <div className="p-6 text-3xl font-bold text-blue-500">
      Hello, Tailwind!
    </div>
  );
}

export default App;
```

Run your application again:

```bash
npm run dev
```

Step 3: Install and Initialize shadcn/ui
shadcn/ui is a CLI tool that adds pre-built components directly to your project.

Initialize shadcn/ui
Run the initialization command:

```bash
npx shadcn@latest init
```

Answer the prompts according to your preferences (e.g., choose Neutral as the base color).

Configure TypeScript path aliases
Edit tsconfig.json:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Edit tsconfig.app.json similarly:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Update Vite configuration for path aliases
First, install type definitions for Node.js:

```bash
npm install -D @types/node
```

Then, update your vite.config.ts:

```javascript
import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

Step 4: Add shadcn/ui Components
You can now add components from shadcn/ui easily.

For example, to add a Button component:

```bash
npx shadcn@latest add button
```

Update src/App.tsx to use the Button:

```javascript
import { Button } from "@/components/ui/button";

function App() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <Button>Click me</Button>
    </div>
  );
}

export default App;
```

Run your application again:

```bash
npm run dev
```