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


def clean_words_from_string(input_str):
    clean_input = clean_string(input_str)
    return clean_input.split()

def graph_from_clean_words(clean_words, n=1):
    """
    each word is a node
    connects start of a kgram with other kgrams
    where 1 <= k <= n
    add extra node to make sure last word is processed
    """
    G = nx.Graph()
    G.add_nodes_from(range(len(clean_words)+1))
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
    if clean_query_str == "":
        return uri_list
    results = SPOTIFY_OBJ.search(q=clean_query_str, limit=limit)
    for song in results["tracks"]["items"]:
        clean_song_name = clean_string(song["name"])
        if clean_song_name == clean_query_str:
            uri_list.append(song["uri"])
    return uri_list

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
        else :
            uri_dict[word_string] = uris
            if output:
                print(word_string, "song exists")
    return G, uri_dict

def parse_path(word_list, path):
    """
    given a path as a list of integer indexes into
    the word list
    compute phrases that make up the complete song
    """
    if len(path) == 0:
        return []
    phrases = []
    for idx in range(len(path)-1):
        start = path[idx]
        end = path[idx+1]
        word_sublist = word_list[start:end]
        word_string = " ".join(word_sublist)
        phrases.append(word_string)
    return phrases


def generate_playlist_from_text(input_str, n=4, output=False):
    """
    will check upto 4grams
    returns all paths as LIST OF DICTS
    where each dict is one path, and in a dict,
    where key is phrase
    and value is spotify uri
    """
    clean_words = clean_words_from_string(input_str)
    empty_graph = graph_from_clean_words(clean_words)
    kgram_graph = connect_kgrams(empty_graph, n=n)
    final_graph, uri_dict = \
    remove_kgrams_with_no_songs(kgram_graph, clean_words, 
        output=output)
    if output:
        print("computed kgrams for all k")
        print("graph has", len(clean_words)+1, "nodes")
        print("graph edges", list(final_graph.edges()))
    source = 0
    target = len(clean_words)
    all_paths_generator = \
        nx.all_simple_paths(final_graph, source, target)
    word_paths = []
    for path in all_paths_generator:
        word_paths.append(parse_path(clean_words, path))

    word_path_dict_list = []
    for word_path in word_paths:
        word_path_dict = {}
        for word in word_path:
            word_path_dict[word] = uri_dict[word]
        word_path_dict_list.append(word_path_dict)
    if output:
        print("final word paths :", word_paths)
    return word_path_dict_list




if __name__ == "__main__":
    test_str = "505 plus 747 equals 1252"
    songs_dict = generate_playlist_from_text(test_str, output=True)
    # print(songs_dict)