/**
 * Central Vuex store
 */

import Vue from "vue";
import Vuex from "vuex";
import createCache from "vuex-cache";

import { gridSearchStore } from "./gridSearchStore";
import { tagStore } from "./tagStore";
import { jobMetricsStore } from "./jobMetricsStore";
import { invocationStore } from "./invocationStore";
import { historyStore } from "./historyStore";
import { userStore } from "./userStore";
import { configStore } from "./configStore";
import { workflowStore } from "./workflowStore";
<<<<<<< HEAD
import { historyStore } from "./historyStore";
=======
>>>>>>> 2d5f7e9d3573eb3bd61e66e5785caecb50adb3ae

Vue.use(Vuex);

export function createStore() {
    return new Vuex.Store({
        plugins: [
            createCache(),
            store => {
                store.dispatch("user/$init", { store });
                store.dispatch("config/$init", { store });
            }
        ],
        modules: {
            gridSearch: gridSearchStore,
            histories: historyStore,
            tags: tagStore,
            jobMetrics: jobMetricsStore,
            invocations: invocationStore,
            user: userStore,
            config: configStore,
<<<<<<< HEAD
            workflows: workflowStore,
            history: historyStore
=======
            workflows: workflowStore
>>>>>>> 2d5f7e9d3573eb3bd61e66e5785caecb50adb3ae
        }
    });
}

const store = createStore();

export default store;
