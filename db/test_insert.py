from db.create_tables import SessionLocal, Note

db = SessionLocal()

# Insert a sample note
new_note = Note(
    content="This is a test note",
    summary="Test summary",
    tags="test,example"
)

db.add(new_note)
db.commit()
db.refresh(new_note)
print(f"Inserted note with ID {new_note.id}")
db.close()
