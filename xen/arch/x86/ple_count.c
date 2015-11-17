unsigned long long ple_count = 0;

void do_set_ple_count(unsigned long long num){
	ple_count = num;
}

unsigned long long do_get_ple_count(void){
	return	ple_count;
}
