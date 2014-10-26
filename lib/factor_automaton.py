import argparse


def build_automaton(strings):
    word_lists = [string.split() for string in strings]
    states = range(sum(map(len, word_lists)) + 4)
    transitions = [(0, 3, '<s>'), (1, 2, '</s>'), (2, '', ''), (3, 1, '<eps>')]
    state = 4
    for word_list in word_lists:
        for i, word in enumerate(word_list):
            transitions.append((3, state, word))
            if word == word_list[-1]:
                transitions.append((state, 3, '<eps>'))
            else:
                transitions.append((state, 3, '<eps>', 0.1))
                transitions.append((state, state, '<eps>', 0.1))
                transitions.append((state, state + 1, word_list[i + 1], 0.8))
            state += 1
    transitions = map(lambda x: x if len(x) >= 4 else x + ("",), transitions)
    transitions = map(lambda x: x if len(x) >= 5 else x + (x[2],), transitions)
    transitions.sort()
    return '\n'.join(['%s\t%s\t%s\t%s\t%s' % (start, to, inl, out, prob) for start, to, inl, prob, out in transitions])


def main():
    parser = argparse.ArgumentParser(
        description="Generate automaton from corpus")
    parser.add_argument('corpus')
    parser.add_argument('-f', action='store_true')
    parser.add_argument('-w', action='store_true')
    args = parser.parse_args()
    if args.f:
        with open(args.corpus) as c:
            print build_automaton(list(c))
    elif args.w:
        with open(args.corpus) as w:
            words = ' '.join(list(w)).split()
            all_words = []
            [all_words.append(word) for word in words if word not in all_words]
            all_words.append('<eps>')
            all_words.append('<s>')
            all_words.append('</s>')
            all_words.append('#0')
            print '\n'.join("%s %s" % (word, i)  for i, word in enumerate(all_words))
    else:
        print build_automaton([args.corpus])

if __name__ == '__main__':
    main()