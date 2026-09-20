'use strict';

const fs = require('fs');            // ArangoDB's built‑in fs module
const users = require("@arangodb/users");
const db = require("@arangodb").db;

// --- Load .env file ---
function loadEnv(path) {
  const content = fs.read(path);
  const lines = content.split('\n');

  const env = {};
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const [key, ...rest] = trimmed.split('=');
    env[key] = rest.join('=');
  }
  return env;
}

const env = loadEnv('arango.env');

// Extract variables
const databaseName = env.MOVIES_DATABASE_NAME;
const moviesUserName = env.MOVIES_DATABASE_USERNAME;
const moviesUserNamePassword = env.MOVIES_PASSWORD;

// --- Your existing logic ---

const allusers = users.all();
const alldatabases = db._databases();

// Create DB if missing
if (!alldatabases.includes(databaseName)) {
  console.log('No Database currently exists so Creating');
  db._createDatabase(databaseName);
} else {
  console.log("Movies Database Already Created");
}


// Create user if missing
const userexists = allusers.find(u => u.user === moviesUserName);

if (!userexists) {
  console.log('No Movies SuperUser exists so creating');
  users.save(moviesUserName, moviesUserNamePassword);
  users.grantDatabase(moviesUserName, databaseName, 'rw');
} else {
  console.log(userexists);
}