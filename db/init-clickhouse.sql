CREATE TABLE IF NOT EXISTS my_table
(
    id UInt32,
    name String,
    age UInt32
) ENGINE = MergeTree()
ORDER BY id;
