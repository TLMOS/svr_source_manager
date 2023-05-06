CREATE TABLE "user"
(
  id SERIAL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "password" VARCHAR(256) NOT NULL,
  max_sources INT NOT NULL DEFAULT 5,
  is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE ("name")
);

CREATE TABLE source
(
  id SERIAL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "url" TEXT NOT NULL,
  status_code INT NOT NULL,
  status_msg TEXT,
  user_id INT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES "user"(id)
);

CREATE TABLE video_chunk
(
  id SERIAL PRIMARY KEY,
  file_path TEXT NOT NULL,
  start_time FLOAT NOT NULL,
  end_time FLOAT NOT NULL,
  source_id INT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES source(id),
  UNIQUE (file_path)
);
