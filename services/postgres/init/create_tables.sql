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
  frame_count INT NOT NULL,
  source_id INT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES source(id),
  UNIQUE (file_path)
);

CREATE INDEX CONCURRENTLY "index_source_id_and_status"
ON source using btree (id, status_code);

CREATE INDEX CONCURRENTLY "index_video_chunk_source_id"
ON video_chunk using btree (source_id);

INSERT INTO source ("name", "url", status_code, status_msg)
VALUES ('test', 'https://archive.org/download/Rick_Astley_Never_Gonna_Give_You_Up/Rick_Astley_Never_Gonna_Give_You_Up.mp4', 1, '');