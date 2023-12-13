from flask import Flask, render_template, request
from FamilyTree import *

app = Flask(__name__)

uri = "neo4j+ssc://4aa3de34.databases.neo4j.io"
username = "neo4j"
password = "567Wy4jvM4bVrlAHLijxVK0k29H3hXha3_itMSXkzMU"
family_tree = FamilyTree(uri, username, password)

@app.teardown_appcontext
def close_driver(exception):
    family_tree.close()

@app.route('/')
def display_family_tree():
    nodes, edges = family_tree.get_family_tree()
    return render_template('index.html', nodes=nodes, edges=edges)

@app.route('/person/<int:person_id>')
def display_person(person_id):
    person_info = family_tree.get_person_info(person_id)

    return render_template('person.html', data=person_info)

@app.route("/add_child", methods=['POST'])
def add_child():
    id = request.form.get('id')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    gender = request.form.get('gender')
    birth = request.form.get('birth')
    death = request.form.get('death')
    parent_id = request.form.get('parent_id')

    new_child = Person(id, first_name, last_name, gender, birth, death)
    
    family_tree.add_child(new_child)
    
    nodes, edges = family_tree.get_family_tree()

    return render_template('index.html', nodes=nodes, edges=edges)


if __name__ == '__main__': app.run(debug=True)