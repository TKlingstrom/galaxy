<<<<<<< HEAD
export const state = {
    historiesById: {}
};

=======
>>>>>>> 2d5f7e9d3573eb3bd61e66e5785caecb50adb3ae
import Vue from "vue";
import { getAppRoot } from "onload/loadConfig";
import axios from "axios";

<<<<<<< HEAD
const getters = {
    getHistoryById: state => historyId => {
        return state.historiesById[historyId];
=======
const state = {
    historyDetailsById: {},
    historyById: {}
};

const getters = {
    getHistoryById: state => historyId => {
        return state.historyById[historyId];
    },
    getHistoryNameById: state => historyId => {
        const details = state.historyDetailsById[historyId];
        if (details && details.name) {
            return details.name;
        } else {
            return "Unavailable";
        }
>>>>>>> 2d5f7e9d3573eb3bd61e66e5785caecb50adb3ae
    }
};

const actions = {
<<<<<<< HEAD
=======
    fetchHistories: async ({ commit }) => {
        const { data } = await axios.get(`${getAppRoot()}api/histories`);
        commit("saveHistories", { histories: data });
    },
>>>>>>> 2d5f7e9d3573eb3bd61e66e5785caecb50adb3ae
    fetchHistoryForId: async ({ commit }, historyId) => {
        const params = {};
        const { data } = await axios.get(`${getAppRoot()}api/histories/${historyId}`, { params });
        commit("saveHistoryForId", { historyId, historyData: data });
    }
};

const mutations = {
<<<<<<< HEAD
    saveHistoryForId: (state, { historyId, historyData }) => {
        Vue.set(state.historiesById, historyId, historyData);
=======
    saveHistories: (state, { histories }) => {
        const historyDetailsById = {};
        histories.forEach(x => {
            historyDetailsById[x.id] = x;
        });
        state.historyDetailsById = historyDetailsById;
    },
    saveHistoryForId: (state, { historyId, historyData }) => {
        Vue.set(state.historyById, historyId, historyData);
>>>>>>> 2d5f7e9d3573eb3bd61e66e5785caecb50adb3ae
    }
};

export const historyStore = {
    state,
    getters,
    actions,
    mutations
};
