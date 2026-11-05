# RetailFlow

RetailFlow is a data engineering and ETL monitoring dashboard for managing data
sources, pipelines, data quality, execution history, and logs. The current
dashboard uses sample data defined in `lib/api.ts`; it does not require a
database or environment variables.

## Run locally

Requirements: Node.js 20.9 or later and npm.

1. Install dependencies:

   ```sh
   npm ci
   ```

2. Start the development server:

   ```sh
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000).

To create and run a production build locally:

```sh
npm run build
npm start
```
