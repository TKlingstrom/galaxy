<template>
    <invocations
<<<<<<< HEAD
        :invocationItems="invocationItems"
        :loading="loading"
        :showTitle="showTitle"
        :simplified="simplified"
        headerMessage="Your most recent workflow invocations are displayed on this page."
        noInvocationsMessage="There are no workflow invocations to show."
=======
        :invocation-items="invocationItems"
        :loading="loading"
        header-message="Your most recent workflow invocations are displayed on this page."
        no-invocations-message="There are no workflow invocations to show."
>>>>>>> 2d5f7e9d3573eb3bd61e66e5785caecb50adb3ae
    >
    </invocations>
</template>

<script>
import Invocations from "../Workflow/Invocations";
import { getRecentInvocations } from "./UserServices";

export default {
    components: {
        Invocations
    },
<<<<<<< HEAD
    props: {
        showTitle: {
            type: Boolean,
            default: true
        },
        simplified: {
            type: Boolean,
            default: false
        }
    },
=======
>>>>>>> 2d5f7e9d3573eb3bd61e66e5785caecb50adb3ae
    data() {
        return {
            invocationItems: [],
            loading: true
        };
    },
    created() {
        getRecentInvocations()
            .then(response => {
                this.invocationItems = response.data;
                this.loading = false;
            })
            .catch(this.handleError);
    },
    methods: {
        handleError(error) {
            console.error(error);
        }
    }
};
</script>
