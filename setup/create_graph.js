var graph_module = require("@arangodb/general-graph");

graph_module._create(
  "Movie_Graph_Direct",
  [
    {
      collection: "movie_edges_direct",
      from: ["title_basics"],
      to: ["name_basics"]
    }
  ]
);
