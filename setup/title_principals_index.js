'use strict';
const db = require('@arangodb').db;
const analyzers = require("@arangodb/analyzers");

db.title_principals.ensureIndex({
  type: "inverted",
  name: "title_principals_inverted_full",
  fields: [
    // Exact-match fields
    { name: "tconst", analyzer: "identity", features: [] },
    { name: "nconst", analyzer: "identity", features: [] },
    { name: "ordering", analyzer: "identity", features: [] },

    // Normalized text fields
    { name: "category", analyzer: "norm_lower_noacc", features: ["norm"] },
    { name: "job", analyzer: "norm_lower_noacc", features: ["norm"] },

    // Full-text field
    { name: "characters", analyzer: "text_en", features: ["frequency", "position", "norm"] }
  ],

  // No primarySort — identity fields cannot be sorted
  // No storedValues — optional, but safest to omit for now

  cleanupIntervalStep: 2,
  commitIntervalMsec: 1000,
  consolidationIntervalMsec: 5000,
  consolidationPolicy: {
    type: "tier",
    segmentsBytesMax: 8589934592,
    maxSkewThreshold: 0.4,
    minDeletionRatio: 0.5
  }
});
