CREATE TABLE "secret"
(
  id SERIAL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "value" VARCHAR(512),
  "encrypted" BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE ("name")
);

CREATE TABLE source
(
  id SERIAL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "url" TEXT NOT NULL,
  status_code INT NOT NULL,
  status_msg TEXT
);

CREATE TABLE video_chunk
(
  id SERIAL PRIMARY KEY,
  file_path TEXT NOT NULL,
  start_time FLOAT NOT NULL,
  end_time FLOAT NOT NULL,
  n_frames INT NOT NULL,
  source_id INT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES source(id),
  UNIQUE (file_path)
);

CREATE INDEX CONCURRENTLY "index_source_id_and_status"
ON source using btree (id, status_code);

CREATE INDEX CONCURRENTLY "index_video_chunk_source_id"
ON video_chunk using btree (source_id);
