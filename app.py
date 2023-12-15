from flask import Flask, render_template, request, redirect
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

@app.route('/males')
def get_all_males():
    male_nodes = family_tree.get_all_males()
    return render_template('people.html', people=male_nodes)

@app.route('/females')
def get_all_females():
    female_nodes = family_tree.get_all_females()
    return render_template('people.html', people=female_nodes)

@app.route('/dead')
def get_all_dead():
    dead_nodes = family_tree.get_all_dead()
    return render_template('people.html', people=dead_nodes)

@app.route('/alive')
def get_all_alive():
    alive_nodes = family_tree.get_all_alive()
    return render_template('people.html', people=alive_nodes)

@app.route('/marriages')
def get_all_married():
    married_nodes = family_tree.get_all_marriages()
    return render_template('marriages.html', marriages=married_nodes)

@app.route('/people/add', methods=('GET', 'POST'))
def person_add():
	if request.method == 'POST':
		first_name = request.form['firstName']
		last_name = request.form['lastName']
		gender = request.form['gender']
		birth = request.form['birth']
		death = request.form['death']
		id = family_tree.add_person(first_name, last_name, gender, birth, death)
		return redirect(f'/person/{id}')

	return render_template('person_add.html')


@app.route('/person/<int:id>/edit', methods=('GET', 'POST'))
def person_edit(id):
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        gender = request.form['gender']
        birth = request.form['birth']
        death = request.form['death']
        family_tree.edit_person(id, first_name, last_name, gender, birth, death)
        return redirect(f'/person/{id}')

    person = family_tree.get_person(id)
    return render_template('person_edit.html', person=person)

@app.route('/person/<int:id>/delete')
def person_delete(id):
    family_tree.delete_person(id)
    return redirect("/")

@app.route('/person/<int:id>/add_child', methods=('GET', 'POST'))
def child_add(id):
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        gender = request.form['gender']
        birth = request.form['birth']
        death = request.form['death']
        parent_gender = request.form['parent_gender']
        child_id = family_tree.add_child(id, first_name, last_name, gender, birth, death, parent_gender)
        return redirect(f'/person/{child_id}')

    parent_gender = request.args.get('parent_gender')
    return render_template('person_add.html', parent_gender=parent_gender)

@app.route('/delete_relation/<int:parent_id>/<int:child_id>', methods=['POST'])
def delete_relation(parent_id, child_id):
    if request.method == 'POST':
        family_tree.delete_relation(parent_id, child_id)
        return redirect(f'/person/{parent_id}')

@app.route('/person/<int:id>/add_parent', methods=('GET', 'POST'))
def parent_add(id):
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        gender = request.form['gender']
        birth = request.form['birth']
        death = request.form['death']
        child_gender = request.form['parent_gender']
        child_id = family_tree.add_parent(id, first_name, last_name, gender, birth, death, child_gender)
        return redirect(f'/person/{child_id}')

    child_gender = request.args.get('child_gender')
    return render_template('person_add.html', parent_gender=child_gender)

@app.route('/person/<int:id>/add_spouse', methods=('GET', 'POST'))
def spouse_add(id):
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        gender = request.form['gender']
        birth = request.form['birth']
        death = request.form['death']
        child_id = family_tree.add_spouse(id, first_name, last_name, gender, birth, death)
        return redirect(f'/person/{child_id}')

    child_gender = request.args.get('child_gender')
    return render_template('person_add.html', parent_gender=child_gender)

@app.route('/create_relationship/<int:node1>/<int:node2>', methods=['GET', 'POST'])
def create_relationship(node1, node2):
    if request.method == 'POST':
        relationship = request.form['relationship']
        gender2 = request.form['node2_gender']
        family_tree.create_relationship(node1, node2, relationship, gender2)
        return redirect('/')
    
    person1 = family_tree.get_person(node1)
    person2 = family_tree.get_person(node2)
    return render_template('create_relationship.html', person1=person1, person2=person2)

if __name__ == '__main__': app.run()