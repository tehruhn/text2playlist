import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import networkx as nx

def connect_to_spotify():
    client_id = os.environ.get('SPOTIFY_CLIENT_ID')
    secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, 
        client_secret=secret)
    try :
        spotify_obj = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    except :
        raise ValueError("Couldn't connect to Spotify")
    return spotify_obj


SPOTIFY_OBJ = connect_to_spotify()


def clean_string(input_str):
    """
    to lowercase
    remove trailing spaces
    remove multispaces and tabs and newlines
    remove all chars except alnum
    """
    input_str = input_str.lower()
    input_str = " ".join(input_str.split())
    clean_str = ""
    for x in input_str:
        if x.isalnum() or x == " ":
            clean_str += x
    return clean_str


def graph_from_clean_string(clean_input, n=1):
    """
    each word is a node
    connects start of a kgram with other kgrams
    where 1 <= k <= n
    """
    clean_words = clean_input.split()
    G = nx.Graph()
    G.add_nodes_from(range(len(clean_words)))
    return G


def connect_kgrams(G, n=1):
    """
    takes networkx graph
    makes edges starting from first node
    connects it to an edge k units ahead
    does this for all k where
    1 <= k <= n
    """
    if n < 1:
        raise ValueError("can't connect these nodes")
    nodes = list(G.nodes())
    last_node = nodes[-1]
    for k in range(1, n+1):
        for node in nodes:
            if node+k <= last_node:
                G.add_edge(node, node+k)
    return G


def find_song_on_spotify(clean_query_str, limit=50):
    """
    returns list of URIs satisfying
    """
    uri_list = []
    results = SPOTIFY_OBJ.search(q=clean_query_str, limit=limit)
    for song in results["tracks"]["items"]:
        clean_song_name = clean_string(song["name"])
        if clean_song_name == clean_query_str:
            uri_list.append(song["uri"])
    return uri_list

# print(find_song_on_spotify("dont"))

def remove_kgrams_with_no_songs(G, clean_input_words, output=False):
    """
    from the input cleaned word list,
    generate all kgrams where 1 <= k <= n
    then query spotify for these kgrams
    remove edges if result not found
    cache obtained uris
    """
    edge_list = list(G.edges())
    uri_dict = {}
    for edge in edge_list:
        start = edge[0]
        end = edge[1]
        word_sublist = clean_input_words[start:end]
        word_string = " ".join(word_sublist)
        uris = find_song_on_spotify(word_string)
        if uris == [] :
            G.remove_edge(start, end)
            if output:
                print(word_string, "edge removed")
        else :
            uri_dict[edge] = uris
            if output:
                print(word_string, "song exists")
    return G, uri_dict

def generate_playlist_from_text(input_str, n=4, output=False):
    """
    will check upto 4grams
    returns all_paths
    """
    clean_input = clean_string(input_str)
    if output :
        print("cleaned string")
    clean_words = clean_input.split()
    empty_graph = graph_from_clean_string(clean_input)
    kgram_graph = connect_kgrams(empty_graph, n=n)
    if output :
        print("computed kgrams for all k")
    final_graph, uri_dict = \
    remove_kgrams_with_no_songs(kgram_graph, clean_words, 
        output=output)
    source = 0
    target = len(clean_words)-1
    all_paths_generator = \
        nx.all_simple_paths(final_graph, source, target)
    paths = []
    for path in all_paths_generator:
        paths.append(path)
    return paths

test_str = "Bye guys thanks for everything"
paths = generate_playlist_from_text(test_str, output=True)
print(paths)