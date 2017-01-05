from repositories.data.repository_pickle import *

if __name__ == "__main__":
    for c in DataStore.get_countries_list():
        print c, c.place_summary
        for a in c.areas:
            print u' '.join((" - ", a.name)).encode('utf-8').strip()
