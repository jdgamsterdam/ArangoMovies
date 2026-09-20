'use strict';
const db = require('@arangodb').db;
const analyzers = require("@arangodb/analyzers");

// Helper: create index only if missing
function ensureIndexIfMissing(collection, indexDef) {
  const existing = collection.getIndexes().find(idx => idx.name === indexDef.name);
  if (!existing) {
    collection.ensureIndex(indexDef);
    console.log(`Created index: ${collection.name()}.${indexDef.name}`);
  } else {
    console.log(`Index already exists: ${collection.name()}.${indexDef.name}`);
  }
}

// Helper: create view only if missing
function ensureViewIfMissing(viewName, type, properties) {
  let view = db._view(viewName);
  if (!view) {
    view = db._createView(viewName, type);
    console.log(`Created view: ${viewName}`);
  } else {
    console.log(`View already exists: ${viewName}`);
  }

  // Always update properties (safe + idempotent)
  view.properties(properties, true);
  return view;
}

// ----------------------------
// Indexes
// ----------------------------

// name_basics
ensureIndexIfMissing(db.name_basics, {
  type: "persistent",
  fields: ["primaryName"],
  name: "myName",
  inBackground: true
});

// title_basics
ensureIndexIfMissing(db.title_basics, {
  type: "persistent",
  fields: ["primaryTitle"],
  name: "myTitle",
  inBackground: true
});


// ----------------------------
// Views
// ----------------------------

// name_basics view
ensureViewIfMissing(
  "name_basics_primaryName_view",
  "arangosearch",
  {
    links: {
      name_basics: { includeAllFields: true }
    }
  }
);

// title_basics view
ensureViewIfMissing(
  "title_basics_view",
  "arangosearch",
  {
    links: {
      title_basics: { includeAllFields: true }
    }
  }
);

// title_principals_search_alias view
ensureViewIfMissing(
  "title_principals_search_alias",
  "search-alias",
  {
    indexes: [
      {
        collection: "title_principals",
        index: "title_principals_inverted_full"
      }
    ]
  }
);

