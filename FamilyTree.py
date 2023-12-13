from neo4j import GraphDatabase

class FamilyTree:
    def __init__(self, uri, user, password):
        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver.verify_connectivity()
        except:
            self.close()

    def close(self):
        self._driver.close()

    def get_family_tree(self):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (n), ()-[r]->()
                RETURN COLLECT(distinct n) AS nodes,
                COLLECT(distinct r) AS relationships
                """)

            nodes = []
            edges = []
            for record in result:
                for node in record['nodes']:
                    nodes.append({'id': node['id'], 'label': node['last_name'] + " " +  node['first_name']})

                for relationship in record['relationships']:
                    start_node = relationship.start_node
                    end_node = relationship.end_node
                    rel_type = relationship.type.lower()
                    edges.append({'from': start_node['id'], 'to': end_node['id'], 'relation': rel_type, 'arrows': 'middle'})

            return nodes, edges
        
    def get_person_info(self, person_id):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (person:Person {id: $person_id})
                OPTIONAL MATCH (person)-[:FATHER|MOTHER]->(child)
                OPTIONAL MATCH (person)<-[:FATHER|MOTHER]-(parent)
                OPTIONAL MATCH (person)-[:HUSBAND|WIFE]->(spouse)
                RETURN person, COLLECT(DISTINCT child) AS children, COLLECT(parent) AS parents, COLLECT(spouse) AS spouses
                """, person_id=person_id)

            person_info = {}
            for record in result:
                person_info['person'] = record['person']
                person_info['children'] = record['children']
                person_info['parents'] = record['parents']
                person_info['spouses'] = record['spouses']
            
            if len(person_info.get('children', [])) == 0:
                del person_info['children']
                
            if len(person_info.get('parents', [])) == 0:
                del person_info['parents']
            
            return person_info
        
    def add_child(self, Person):
        with db.session() as session:
            session.run(
                "CREATE (p:Person {id: $id, first_name: $first_name, last_name: $last_name, gender: $gender, birth: $birth, death: $death})",
                id=new_child.id,
                first_name=new_child.first_name,
                last_name=new_child.last_name,
                gender=new_child.gender,
                birth=new_child.birth,
                death=new_child.death
            )
            
            session.run(
                "MATCH (parent:Person {id: $parent_id}), (child:Person {id: $child_id}) CREATE (parent)-[:PARENT_OF]->(child)",
                parent_id=parent_id,
                child_id=new_child.id
            )
            
            session.run(
                "MATCH (parent:Person {id: $parent_id}), (child:Person {id: $child_id}) CREATE (parent)-[:PARENT_OF]->(child) CREATE (child)-[:CHILD_OF]->(parent)",
                parent_id=parent_id,
                child_id=new_child.id
            )
        
class Person:
    def __init__(self, id, first_name, last_name, gender, birth, death):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.birth = birth
        self.death = death