#include "alternation_open_list.h"

#include "../open_list.h"

#include "../plugins/plugin.h"
#include "../utils/memory.h"
#include "../utils/system.h"

#include <cassert>
#include <memory>
#include <vector>
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
    const vector<float> probs;
protected:
    virtual void do_insertion(EvaluationContext &eval_context,
                              const Entry &entry) override;

public:
    explicit AlternationOpenList(const plugins::Options &opts);
    virtual ~AlternationOpenList() override = default;

    virtual Entry remove_min() override;
    virtual bool empty() const override;
    virtual void clear() override;
    virtual void boost_preferred() override;
    virtual void get_path_dependent_evaluators(
        set<Evaluator *> &evals) override;
    virtual bool is_dead_end(
        EvaluationContext &eval_context) const override;
    virtual bool is_reliable_dead_end(
        EvaluationContext &eval_context) const override;
    std::mt19937 rng;
};


template<class Entry>
AlternationOpenList<Entry>::AlternationOpenList(const plugins::Options &opts)
    : boost_amount(opts.get<int>("boost")), 
    decision(opts.get<int>("decision")), 
    rng(opts.get<int>("seed")), // std::random_device{}()
    probs(opts.get_list<float>("probs")) { 
    vector<shared_ptr<OpenListFactory>> open_list_factories(
        opts.get_list<shared_ptr<OpenListFactory>>("sublists"));
    open_lists.reserve(open_list_factories.size());
    for (const auto &factory : open_list_factories)
        open_lists.push_back(factory->create_open_list<Entry>());

    priorities.resize(open_lists.size(), 0);
}

template<class Entry>
void AlternationOpenList<Entry>::do_insertion(
    EvaluationContext &eval_context, const Entry &entry) {
    for (const auto &sublist : open_lists)
        sublist->insert(eval_context, entry);
}

template<class Entry>
Entry AlternationOpenList<Entry>::remove_min() {
    int best = -1;
    std::vector<int> non_empty_lists;
    vector<float> non_empty_probs;
    vector<float> empty_probs;
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
    }
    else {
        cout << "Invalid decision value" << endl;
        utils::exit_with(ExitCode::SEARCH_CRITICAL_ERROR);
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
        add_option<vector<float>>(
            "probs",
            "probabilities for selecting each open list",
            "[]");
    }

    virtual shared_ptr<AlternationOpenListFactory> create_component(const plugins::Options &options, const utils::Context &context) const override {
        plugins::verify_list_non_empty<shared_ptr<OpenListFactory>>(context, options, "sublists");
        if (options.get<int>("decision") == 2) {
            plugins::verify_list_non_empty<float>(context, options, "probs");
            const vector<float> probs = options.get_list<float>("probs").size();
            const int probs_len = options.get_list<float>("probs").size();
            const int sublists_len = options.get_list<shared_ptr<OpenListFactory>>("sublists").size();
            if (probs_len != sublists_len) {
                cout << "Invalid probabilities size" << endl;
                utils::exit_with(ExitCode::SEARCH_CRITICAL_ERROR);
            }
            float sum = 0.0;
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
