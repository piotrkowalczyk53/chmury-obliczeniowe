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
                MATCH (n:Person)
                OPTIONAL MATCH (n:Person)-[r]->()
                RETURN COLLECT(DISTINCT n) AS nodes, COLLECT(DISTINCT r) AS relationships
                """)
            nodes = []
            edges = []
            for record in result:
                for node in record['nodes']:
                    nodes.append({'id': node.id, 'label': node['last_name'] + " " + node['first_name']})

                for relationship in record['relationships']:
                    start_node = relationship.start_node
                    end_node = relationship.end_node
                    rel_type = relationship.type.lower()
                    edges.append({'from': start_node.id, 'to': end_node.id, 'relation': rel_type, 'arrows': 'middle'})

            return nodes, edges

        
    def get_person_info(self, person_id):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (person:Person)
                WHERE id(person) = $person_id
                OPTIONAL MATCH (person)-[:FATHER|MOTHER]->(child)
                OPTIONAL MATCH (person)<-[:FATHER|MOTHER]-(parent)
                OPTIONAL MATCH (person)-[:SPOUSE]->(spouse)
                RETURN person, COLLECT(child) AS children, COLLECT(parent) AS parents, COLLECT(spouse) AS spouses
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
                
            if len(person_info.get('spouses', [])) == 0:
                del person_info['spouses']
            
            return person_info
    
    def get_person(self, person_id):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (person:Person)
                WHERE id(person) = $person_id
                RETURN person AS person
                """, person_id=person_id)

            record = result.single()
            return record['person']
        
    def edit_person(self, person_id, first_name, last_name, gender, birth, death):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (person:Person)
                WHERE id(person) = $person_id
                SET person.first_name = $first_name,
                    person.last_name = $last_name,
                    person.gender = $gender,
                    person.birth = date($birth),
                    person.death = date($death)
                RETURN person
                """, person_id=person_id, first_name=first_name, last_name=last_name,
                                 gender=gender, birth=birth, death=death)
            
    def delete_person(self, person_id):
        with self._driver.session() as session:
            session.run(
                """
                MATCH (person:Person)
                WHERE id(person) = $person_id
                DETACH DELETE person
                """,
                person_id=person_id,
            )
        
    def get_all_males(self):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (person:Person {gender: 'Male'})
                RETURN person
                """)
            
            nodes = [record['person'] for record in result]
            return nodes
        
    def get_all_females(self):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (person:Person {gender: 'Female'})
                RETURN person
                """)
            
            nodes = [record['person'] for record in result]
            return nodes
            
    def get_all_dead(self):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (person:Person)
                WHERE person.death < date()
                RETURN person
                """)
        
            nodes = [record['person'] for record in result]
            return nodes
            
    def get_all_alive(self):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (person:Person)
                WHERE person.death IS NULL OR person.death = ''
                RETURN person
                """)
            
            nodes = [record['person'] for record in result]
            return nodes
        
    def get_all_marriages(self):
        with self._driver.session() as session:
            result = session.run("""
                MATCH (h:Person {gender: 'Male'})-[marriage:MARRIAGE]->(w:Person)
                RETURN COLLECT(DISTINCT [h, w, marriage]) AS marriages
                """)
            
            marriages = [marriage for record in result for marriage in record['marriages']]
            return marriages if marriages else []
        
    def add_person(self, first_name, last_name, gender, birth, death):
        with self._driver.session() as session:
            result = session.run("""
                CREATE (p:Person {
                first_name: $first_name,
                last_name: $last_name,
                gender: $gender,
                birth: date($birth),
                death: date($death)
            })
            RETURN id(p) AS person_id
            """, first_name=first_name, last_name=last_name, gender=gender, birth=birth, death=death)

            return result.single()['person_id']
        
    def add_child(self, person_id, first_name, last_name, gender, birth, death, parent_gender):
        with self._driver.session() as session:
            relationship_type = "FATHER" if parent_gender == "Male" else "MOTHER"

            query = """
                MATCH (parent:Person)
                WHERE id(parent) = $person_id
                CREATE (child:Person {
                    first_name: $first_name,
                    last_name: $last_name,
                    gender: $gender,
                    birth: date($birth)
                    %s
                })
                CREATE (parent)-[:%s]->(child)
                CREATE (parent)<-[:%s]-(child)
                """ % (", death: date($death)" if death else "", relationship_type, "DAUGHTER" if gender == "Female" else "SON")

            parameters = {
                "person_id": person_id,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "birth": birth,
                "death": death
            }

            session.run(query, **parameters)

            return person_id
        
    def add_parent(self, person_id, first_name, last_name, gender, birth, death, child_gender):
        with self._driver.session() as session:
            relationship_type = "SON" if child_gender == "Male" else "DAUGHTER"
            parent_relationship = "MOTHER" if gender == "Female" else "FATHER"

            query = """
                    MATCH (child:Person)
                    WHERE id(child) = $person_id

                    OPTIONAL MATCH (old_parent:Person)-[old_relation:%s]->(child:Person)
                    WHERE id(child) = $person_id
                    DELETE old_relation

                    CREATE (parent:Person {
                        first_name: $first_name,
                        last_name: $last_name,
                        gender: $gender,
                        birth: date($birth)
                        %s
                    })
                    CREATE (child)-[:%s]->(parent)
                    CREATE (child)<-[:%s]-(parent)
                    """ % (
                        parent_relationship,
                        ", death: date($death)" if death else "",
                        relationship_type,
                        parent_relationship
                    )

            parameters = {
                "person_id": person_id,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "birth": birth,
                "death": death
            }

            session.run(query, **parameters)

            return person_id
        
    def add_spouse(self, person_id, first_name, last_name, gender, birth, death):
        with self._driver.session() as session:
            query = """
                    MATCH (me:Person)
                    WHERE id(me) = $person_id

                    OPTIONAL MATCH (ex:Person)-[divorce:MARRIAGE]-(me:Person)
                    WHERE id(me) = $person_id
                    SET divorce.divorce_date = date(datetime())

                    CREATE (new:Person {
                        first_name: $first_name,
                        last_name: $last_name,
                        gender: $gender,
                        birth: date($birth)
                        %s
                    })

                    CREATE (me)-[new_m:MARRIAGE]->(new)
                    CREATE (me)<-[new_m2:MARRIAGE]-(new)
                    SET new_m.marriage_date = date(datetime())
                    SET new_m2.marriage_date = date(datetime())
                    """ % (
                        ", death: date($death)" if death else ""
                    )

            parameters = {
                "person_id": person_id,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "birth": birth,
                "death": death
            }

            session.run(query, **parameters)

            return person_id

    def delete_relation(self, parent_id, child_id):
        with self._driver.session() as session:
            relation_query = """
                MATCH (parent:Person)-[rel]->(child:Person)
                WHERE id(parent) = $parent_id AND id(child) = $child_id
                DELETE rel

                MATCH (parent:Person)-[rel]-(child:Person)
                WHERE id(parent) = $parent_id AND id(child) = $child_id
                DELETE rel
            """

            session.run(relation_query, parent_id=parent_id, child_id=child_id)

    def create_relationship(self, node1, node2, relationship, gender2):
        with self._driver.session() as session:
            if relationship == 'FATHER' or relationship == 'MOTHER':
                if gender2 == 'male':
                    relationship2 = 'SON'
                elif gender2 == 'female':
                    relationship2 = 'DAUGHTER'

                session.run("""
                    MATCH (n1:Person), (n2:Person)
                    WHERE id(n1) = $node1_id AND id(n2) = $node2_id
                    CREATE (n1)-[:%s]->(n2)
                    CREATE (n1)<-[:%s]-(n2)
                """, relationship, relationship2, node1_id=node1, node2_id=node2)

            elif relationship == 'MARRIAGE':
                session.run("""
                    MATCH (n1:Person), (n2:Person)
                    WHERE ID(n1) = $node1_id AND ID(n2) = $node2_id
                            
                    OPTIONAL MATCH (n1)-[m1:MARRIAGE]->(n2)
                    WHERE m1.divorce_date IS NULL
                    SET m1.divorce_date = date(datetime())
                    WITH n1, n2, m1
                            
                    OPTIONAL MATCH (n2)-[m2:MARRIAGE]->(n1)
                    WHERE m2.divorce_date IS NULL
                    SET m2.divorce_date = date(datetime())
                    WITH n1, n2, m1, m2
                            
                    WHERE m1 IS NULL AND m2 IS NULL
                    CREATE (n1)-[newm1:MARRIAGE]->(n2)
                    SET newm1.marriage_date = date(datetime())
                    WITH n1, n2, newm1
                            
                    CREATE (n2)-[newm2:MARRIAGE]->(n1)
                    SET newm2.marriage_date = date(datetime())
                """, node1_id=node1, node2_id=node2)