from app.models.user import Class

def get_classes_by_teachers(db, teacher_id):
    classes = db.query(Class.id, Class.name).filter(
        Class.teacher_id == teacher_id
    ).all()
    return [{"id": c.id, "name": c.name} for c in classes]

def is_owned_class(db, class_id, teacher_id):
    clazz = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_id
    ).first()
    if clazz:
        return True
    return False