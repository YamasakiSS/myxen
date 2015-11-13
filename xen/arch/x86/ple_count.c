unsigned int pause_loop_exiting_count;

void do_set_ple_count(unsigned int num){
	pause_loop_exiting_count = num;
}

int do_get_ple_count(void){
	return	pause_loop_exiting_count;
}
