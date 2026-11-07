import os

from ariadne import (
    QueryType,
    ObjectType,
    make_executable_schema,
    graphql_sync,
)
from ariadne.explorer import ExplorerGraphiQL
from flask import Flask, Response, abort, jsonify, render_template, request

from data import STUDENTS
from cv import build_cvs, cv_bytes, cv_url_for

BY_ID = {s["id"]: s for s in STUDENTS}
BY_SLUG = {s["slug"]: s for s in STUDENTS}


def public_students():
    return [s for s in STUDENTS if s["visibility"] == "PUBLIC"]


def all_tags():
    seen = {}
    for s in STUDENTS:
        for t in s["tags"]:
            seen.setdefault(t, t)
    return [{"name": name} for name in sorted(seen)]


type_defs = """
    enum Visibility { PUBLIC PRIVATE }

    type Student {
        id: ID!
        slug: String!
        name: String!
        promo: String!
        headline: String!
        visibility: Visibility!
        tags: [Tag!]!
        cvUrl: String!
    }

    type Tag {
        name: String!
        students: [Student!]!
    }

    type Query {
        students: [Student!]!
        student(id: ID): Student
        studentBySlug(slug: String): Student
        tags: [Tag!]!
    }
"""

query = QueryType()
student_type = ObjectType("Student")
tag_type = ObjectType("Tag")


@query.field("students")
def resolve_students(*_):
    # Listing public : les profils en opposition sont filtrés ici.
    return public_students()


@query.field("student")
def resolve_student(_, __, id=None):
    return BY_ID.get(id)


@query.field("studentBySlug")
def resolve_student_by_slug(_, __, slug=None):
    return BY_SLUG.get(slug)


@query.field("tags")
def resolve_tags(*_):
    return all_tags()


@student_type.field("tags")
def resolve_student_tags(obj, _):
    return [{"name": t} for t in obj["tags"]]


@student_type.field("cvUrl")
def resolve_cv_url(obj, _):
    return cv_url_for(obj["id"])


@tag_type.field("students")
def resolve_tag_students(obj, _):
    # Projection par tag : le filtre de visibilité du listing public
    # n'est pas réappliqué ici.
    return [s for s in STUDENTS if obj["name"] in s["tags"]]


schema = make_executable_schema(type_defs, query, student_type, tag_type)

app = Flask(__name__)
build_cvs()

explorer_html = ExplorerGraphiQL().html(None)


@app.route("/")
def index():
    return render_template("index.html", students=public_students())


@app.route("/api/students")
def api_students():
    return jsonify([
        {
            "id": s["id"],
            "name": s["name"],
            "promo": s["promo"],
            "headline": s["headline"],
            "tags": s["tags"],
        }
        for s in public_students()
    ])


@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return explorer_html, 200


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema,
        data,
        context_value={"request": request},
        introspection=True,
    )
    status = 200 if success else 400
    return jsonify(result), status


@app.route("/cv/<token>.pdf")
def serve_cv(token):
    pdf = cv_bytes(token)
    if pdf is None:
        abort(404)
    return Response(pdf, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
