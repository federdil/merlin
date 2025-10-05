import os
from sqlalchemy import create_engine, text
from .models import Base   # <-- relative import
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# Ensure pgvector extension is enabled and schema is created
with engine.connect() as connection:
    # Enable pgvector extension
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    connection.commit()

# Create tables
Base.metadata.create_all(bind=engine)

with engine.connect() as connection:
    # Ensure columns exist for current schema
    connection.execute(text("ALTER TABLE IF EXISTS notes ADD COLUMN IF NOT EXISTS title VARCHAR"))
    connection.execute(text("ALTER TABLE IF EXISTS notes ADD COLUMN IF NOT EXISTS tags VARCHAR[]"))
    connection.execute(text("ALTER TABLE IF EXISTS notes ADD COLUMN IF NOT EXISTS embedding vector(384)"))
    connection.commit()

# If tags exists but is TEXT (non-array), convert it to VARCHAR[] using regexp_replace
with engine.connect() as connection:
    conversion_sql = text(
        """
        DO $$
        DECLARE
            col_type text;
        BEGIN
            SELECT data_type INTO col_type
            FROM information_schema.columns
            WHERE table_name = 'notes' AND column_name = 'tags';

            IF col_type = 'text' THEN
                ALTER TABLE notes
                ALTER COLUMN tags TYPE VARCHAR[]
                USING (
                    CASE
                        WHEN tags IS NULL THEN NULL
                        WHEN left(tags,1) = '{' THEN (
                            string_to_array(regexp_replace(tags, '[\"{}]', '', 'g'), ',')
                        )
                        ELSE string_to_array(tags, ',')
                    END
                );
            END IF;
        END
        $$;
        """
    )
    connection.execute(conversion_sql)
    connection.commit()

# Create an IVFFlat index on the embedding column for faster similarity search
with engine.connect() as connection:
    connection.execute(
        text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relkind = 'i'
                      AND c.relname = 'notes_embedding_idx'
                ) THEN
                    CREATE INDEX notes_embedding_idx
                    ON notes USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                END IF;
            END
            $$;
            """
        )
    )
    connection.commit()

print("Tables/columns created, tags normalized to array, and pgvector/index ensured successfully!")
