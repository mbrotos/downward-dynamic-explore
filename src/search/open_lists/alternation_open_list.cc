#include "alternation_open_list.h"

#include "../open_list.h"

#include "../plugins/plugin.h"
#include "../utils/memory.h"
#include "../utils/system.h"
#include "../state_registry.h"

#include <cassert>
#include <memory>
#include <vector>
#include <deque>
#include <random>

using namespace std;
using utils::ExitCode;

namespace alternation_open_list {
template<class Entry>
class AlternationOpenList : public OpenList<Entry> {
    vector<unique_ptr<OpenList<Entry>>> open_lists;
    vector<int> priorities;

    const int boost_amount;
    const int decision;
    vector<double> probs;
    std::mt19937 rng;

    vector<deque<double>> past_g;
    vector<deque<double>> past_f;

    double last_list;
    double max_hist_size = 10;
    double learning_rate = 0.01;
    double max_prob = 0.8;
    double min_prob = 0.2;
protected:
    virtual void do_insertion(EvaluationContext &eval_context,
                              const Entry &entry) override;

public:
    explicit AlternationOpenList(const plugins::Options &opts);
    virtual ~AlternationOpenList() override = default;

    virtual Entry remove_min(StateRegistry* registry = nullptr, double last_f=-1, double last_g=-1) override;
    virtual bool empty() const override;
    virtual void clear() override;
    virtual void boost_preferred() override;
    virtual void get_path_dependent_evaluators(
        set<Evaluator *> &evals) override;
    virtual bool is_dead_end(
        EvaluationContext &eval_context) const override;
    virtual bool is_reliable_dead_end(
        EvaluationContext &eval_context) const override;
};


template<class Entry>
AlternationOpenList<Entry>::AlternationOpenList(const plugins::Options &opts)
    : boost_amount(opts.get<int>("boost")), 
    decision(opts.get<int>("decision")), 
    rng(opts.get<int>("seed")), // std::random_device{}()
    probs(opts.get_list<double>("probs")) { 
    vector<shared_ptr<OpenListFactory>> open_list_factories(
        opts.get_list<shared_ptr<OpenListFactory>>("sublists"));
    open_lists.reserve(open_list_factories.size());
    for (const auto &factory : open_list_factories)
        open_lists.push_back(factory->create_open_list<Entry>());

    priorities.resize(open_lists.size(), 0);

    // for(int i = 0;i < open_lists.size();i++) {
    //     past_g.push_back(deque<double>(0));
    //     past_f.push_back(deque<double>(0));
    // }
    past_g.resize(open_lists.size());
    past_f.resize(open_lists.size());

    last_list = -1;
}

template<class Entry>
void AlternationOpenList<Entry>::do_insertion(
    EvaluationContext &eval_context, const Entry &entry) {
    for (const auto &sublist : open_lists)
        sublist->insert(eval_context, entry);
}

template<class Entry>
Entry AlternationOpenList<Entry>::remove_min(StateRegistry* registry, double last_f, double last_g) {


    if(last_list != -1 && last_g != -1) {
        past_g[last_list].push_back(last_g);
        past_f[last_list].push_back(last_f);

        if(past_g.size() > max_hist_size) {
            past_g[last_list].pop_front();
            past_f[last_list].pop_front();
        }

        vector<double> avg_gs(open_lists.size());
        for(int i = 0;i < open_lists.size();i++) {
            for(int j = 0;j < past_g[i].size();j++) {
                avg_gs[i] += past_g[i][j];
            }
            avg_gs[i] /= past_g[i].size();
        }

        int best_list = 0;
        double best_val = avg_gs[0];
        for(int i = 1;i < open_lists.size();i++) {
            if(avg_gs[i] > best_val) {
                best_val = avg_gs[i];
                best_list = i;
            }
        }

        double cur_min_prob = probs[0];
        for(int i = 1;i < open_lists.size();i++) {
            if(probs[i] < cur_min_prob) 
                cur_min_prob = probs[i];
        }

        if(cur_min_prob - learning_rate >= min_prob || probs[best_list] + learning_rate <= max_prob) {
            for(int i = 0;i < open_lists.size();i++) {
                if(i == best_list)
                    probs[i] += learning_rate;
                else {
                    probs[i] -= (learning_rate / (open_lists.size()-1));
                }
            }

            // cout << "g1: " << avg_gs[0] << " g2: " << avg_gs[1] << "\n";
            // cout << "p1: " << probs[0] << " p2: " << probs[1] << "\n";
        }
        else {
            // cout << "Skipped due to prob limits\n";
        }

    }

    int best = -1;
    std::vector<int> non_empty_lists;
    vector<double> non_empty_probs;
    vector<double> empty_probs;
    for (std::size_t i = 0; i < open_lists.size(); ++i) {
        if (!open_lists[i]->empty()) {
            non_empty_lists.push_back(i);
            if (decision == 2) {
                non_empty_probs.push_back(probs[i]);
            }
            if (best == -1 || priorities[i] < priorities[best]) {
                best = i;
            }
        } else if (decision == 2) {
            empty_probs.push_back(probs[i]);
        }
    }

    


    if (decision == 2) {
        for (std::size_t i = 0; i < empty_probs.size(); ++i) {
            // equally distribute the probabilities of empty open lists to non-empty ones
            for (std::size_t j = 0; j < non_empty_probs.size(); ++j) {
                non_empty_probs[j] += empty_probs[i] / non_empty_probs.size();
            }
        }
    }
    assert(!non_empty_lists.empty()); // Ensure there's at least one non-empty list
    int selected_index = -1;

    if (decision == 0) { // The default alternation strategy
        assert(best != -1);
        const auto &best_list = open_lists[best];
        assert(!best_list->empty());
        ++priorities[best];

        last_list = best;

        return best_list->remove_min();
        
    } else if (decision == 1) { // Random alternation strategy
        std::uniform_int_distribution<> dist(0, non_empty_lists.size() - 1);
        selected_index = non_empty_lists[dist(rng)];
        // cout << "Selected index: " << selected_index << endl;
    }
    else if (decision == 2) { // Weighted-random alternation strategy using probs
        if (non_empty_probs.size() != non_empty_lists.size()) {
            cout << "Invalid probabilities size" << endl;
            utils::exit_with(ExitCode::SEARCH_CRITICAL_ERROR);
        }
        std::discrete_distribution<> dist(non_empty_probs.begin(), non_empty_probs.end());
        selected_index = non_empty_lists[dist(rng)];
        // cout << "Selected index: " << selected_index << endl;
        // // print the probabilities
        // cout << "Probabilities: ";
        // for (std::size_t i = 0; i < non_empty_probs.size(); ++i) {
        //     cout << non_empty_probs[i] << " ";
        // }
    }
    else {
        cout << "Invalid decision value" << endl;
        utils::exit_with(ExitCode::SEARCH_CRITICAL_ERROR);
    }

    last_list = selected_index;

    if(registry != nullptr) {
        auto id = open_lists[selected_index]->remove_min();
        
        if constexpr(is_same_v<Entry, StateID>) {
            State s = (*registry).lookup_state(id);
            // cout << "ID: " << s.get_id() << " F: " << last_f << " G: " << last_g << "\n";
        }
        else {
            State s = (*registry).lookup_state(id.first);
            // cout << "ID2: " << s.get_id() << "\n";
        }
        return id;
    }
    return open_lists[selected_index]->remove_min();
}

template<class Entry>
bool AlternationOpenList<Entry>::empty() const {
    for (const auto &sublist : open_lists)
        if (!sublist->empty())
            return false;
    return true;
}

template<class Entry>
void AlternationOpenList<Entry>::clear() {
    for (const auto &sublist : open_lists)
        sublist->clear();
}

template<class Entry>
void AlternationOpenList<Entry>::boost_preferred() {
    for (size_t i = 0; i < open_lists.size(); ++i)
        if (open_lists[i]->only_contains_preferred_entries())
            priorities[i] -= boost_amount;
}

template<class Entry>
void AlternationOpenList<Entry>::get_path_dependent_evaluators(
    set<Evaluator *> &evals) {
    for (const auto &sublist : open_lists)
        sublist->get_path_dependent_evaluators(evals);
}

template<class Entry>
bool AlternationOpenList<Entry>::is_dead_end(
    EvaluationContext &eval_context) const {
    // If one sublist is sure we have a dead end, return true.
    if (is_reliable_dead_end(eval_context))
        return true;
    // Otherwise, return true if all sublists agree this is a dead-end.
    for (const auto &sublist : open_lists)
        if (!sublist->is_dead_end(eval_context))
            return false;
    return true;
}

template<class Entry>
bool AlternationOpenList<Entry>::is_reliable_dead_end(
    EvaluationContext &eval_context) const {
    for (const auto &sublist : open_lists)
        if (sublist->is_reliable_dead_end(eval_context))
            return true;
    return false;
}


AlternationOpenListFactory::AlternationOpenListFactory(const plugins::Options &options)
    : options(options) {
}

unique_ptr<StateOpenList>
AlternationOpenListFactory::create_state_open_list() {
    return utils::make_unique_ptr<AlternationOpenList<StateOpenListEntry>>(options);
}

unique_ptr<EdgeOpenList>
AlternationOpenListFactory::create_edge_open_list() {
    return utils::make_unique_ptr<AlternationOpenList<EdgeOpenListEntry>>(options);
}

class AlternationOpenListFeature : public plugins::TypedFeature<OpenListFactory, AlternationOpenListFactory> {
public:
    AlternationOpenListFeature() : TypedFeature("alt") {
        document_title("Alternation open list");
        document_synopsis(
            "alternates between several open lists.");

        add_list_option<shared_ptr<OpenListFactory>>(
            "sublists",
            "open lists between which this one alternates");
        add_option<int>(
            "boost",
            "boost value for contained open lists that are restricted "
            "to preferred successors",
            "0");
        add_option<int>(
            "decision",
            "decision value for alternating between open lists",
            "0");
        add_option<int>(
            "seed",
            "seed value for random number generator",
            "42");
        add_list_option<double>(
            "probs",
            "probabilities for selecting each open list",
            "[]");
    }

    virtual shared_ptr<AlternationOpenListFactory> create_component(const plugins::Options &options, const utils::Context &context) const override {
        plugins::verify_list_non_empty<shared_ptr<OpenListFactory>>(context, options, "sublists");
        if (options.get<int>("decision") == 2) {
            plugins::verify_list_non_empty<double>(context, options, "probs");
            const vector<double> probs = options.get_list<double>("probs");
            const int probs_len = probs.size();
            const int sublists_len = options.get_list<shared_ptr<OpenListFactory>>("sublists").size();
            if (probs_len != sublists_len) {
                cout << "Invalid probabilities size" << endl;
                utils::exit_with(ExitCode::SEARCH_CRITICAL_ERROR);
            }
            double sum = 0.0;
            for (int i = 0; i < probs_len; ++i) {
                sum += probs[i];
            }
            if (sum != 1.0) {
                cout << "Invalid probabilities sum" << endl;
                utils::exit_with(ExitCode::SEARCH_CRITICAL_ERROR);
            }
        }
        return make_shared<AlternationOpenListFactory>(options);
    }
};

static plugins::FeaturePlugin<AlternationOpenListFeature> _plugin;
}
